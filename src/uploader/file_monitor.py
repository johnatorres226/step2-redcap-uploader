"""File monitoring and change detection functionality."""

import os
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict


@dataclass
class FileInfo:
    """Information about a processed file."""
    path: str
    hash: str
    size: int
    modified_time: float
    processed_time: str
    records_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileInfo":
        """Create from dictionary."""
        return cls(**data)


class FileMonitor:
    """Monitor files for changes and track processing history."""
    
    def __init__(self, watch_directory: Path, logger: logging.Logger):
        self.watch_directory = Path(watch_directory)
        self.logger = logger
        self.tracking_file = self.watch_directory / "file_tracking.json"
        self._file_history: Dict[str, FileInfo] = {}
        self._load_history()
    
    def _load_history(self) -> None:
        """Load file processing history from disk."""
        if self.tracking_file.exists():
            try:
                with open(self.tracking_file, 'r') as f:
                    data = json.load(f)
                    
                for path, file_data in data.items():
                    self._file_history[path] = FileInfo.from_dict(file_data)
                    
                self.logger.debug(f"Loaded {len(self._file_history)} file records from history")
                
            except Exception as e:
                self.logger.error(f"Error loading file history: {e}")
                self._file_history = {}
        else:
            self.logger.info("No file history found, starting fresh")
    
    def _save_history(self) -> None:
        """Save file processing history to disk."""
        try:
            # Ensure directory exists
            self.tracking_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to serializable format
            data = {path: file_info.to_dict() for path, file_info in self._file_history.items()}
            
            with open(self.tracking_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            self.logger.debug(f"Saved {len(self._file_history)} file records to history")
            
        except Exception as e:
            self.logger.error(f"Error saving file history: {e}")
    
    def get_file_hash(self, file_path: Path, algorithm: str = "sha256") -> str:
        """Calculate file hash."""
        try:
            hash_obj = hashlib.new(algorithm)
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def has_file_changed(self, file_path: Path) -> bool:
        """Check if file has changed since last processing."""
        file_path_str = str(file_path)
        
        if file_path_str not in self._file_history:
            return True  # New file
        
        try:
            current_stats = file_path.stat()
            stored_info = self._file_history[file_path_str]
            
            # Check modification time first (faster)
            if current_stats.st_mtime != stored_info.modified_time:
                return True
            
            # Check size
            if current_stats.st_size != stored_info.size:
                return True
            
            # If modification time and size are the same, assume no change
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking file changes for {file_path}: {e}")
            return True  # Assume changed if we can't determine
    
    def mark_file_processed(self, file_path: Path, records_count: int = 0) -> None:
        """Mark file as processed."""
        try:
            file_stats = file_path.stat()
            file_hash = self.get_file_hash(file_path)
            
            file_info = FileInfo(
                path=str(file_path),
                hash=file_hash,
                size=file_stats.st_size,
                modified_time=file_stats.st_mtime,
                processed_time=datetime.now().isoformat(),
                records_count=records_count
            )
            
            self._file_history[str(file_path)] = file_info
            self._save_history()
            
            self.logger.info(f"Marked file as processed: {file_path.name}")
            
        except Exception as e:
            self.logger.error(f"Error marking file as processed {file_path}: {e}")
    
    def get_file_status(self) -> List[Dict[str, Any]]:
        """Get status of all files in the watch directory."""
        status_list = []
        
        try:
            # Get all files in watch directory
            if not self.watch_directory.exists():
                self.logger.warning(f"Watch directory does not exist: {self.watch_directory}")
                return status_list
            
            for file_path in self.watch_directory.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    try:
                        stats = file_path.stat()
                        is_changed = self.has_file_changed(file_path)
                        
                        file_status = {
                            'file': file_path.name,
                            'path': str(file_path),
                            'size': stats.st_size,
                            'last_modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                            'status': 'CHANGED' if is_changed else 'PROCESSED',
                            'hash': self.get_file_hash(file_path) if is_changed else 
                                   self._file_history.get(str(file_path), FileInfo("", "", 0, 0, "")).hash
                        }
                        
                        # Add processing history if available
                        if str(file_path) in self._file_history:
                            history = self._file_history[str(file_path)]
                            file_status.update({
                                'last_processed': history.processed_time,
                                'records_processed': history.records_count
                            })
                        
                        status_list.append(file_status)
                        
                    except Exception as e:
                        self.logger.error(f"Error getting status for {file_path}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error scanning directory {self.watch_directory}: {e}")
        
        return status_list
    
    def get_new_files(self) -> List[Path]:
        """Get list of new or changed files."""
        new_files = []
        
        try:
            if not self.watch_directory.exists():
                return new_files
            
            for file_path in self.watch_directory.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    if self.has_file_changed(file_path):
                        new_files.append(file_path)
            
            self.logger.info(f"Found {len(new_files)} new/changed files")
            
        except Exception as e:
            self.logger.error(f"Error finding new files: {e}")
        
        return new_files
    
    def cleanup_old_entries(self, days: int = 30) -> None:
        """Remove entries for files that no longer exist or are very old."""
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            to_remove = []
            
            for file_path_str, file_info in self._file_history.items():
                file_path = Path(file_path_str)
                
                # Remove if file doesn't exist or is very old
                if not file_path.exists() or file_info.modified_time < cutoff_time:
                    to_remove.append(file_path_str)
            
            for file_path_str in to_remove:
                del self._file_history[file_path_str]
            
            if to_remove:
                self._save_history()
                self.logger.info(f"Cleaned up {len(to_remove)} old file entries")
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
