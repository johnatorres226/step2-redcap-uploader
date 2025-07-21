"""Change tracking and audit logging functionality."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class FieldChange:
    """Represents a change to a single field."""
    record_id: str
    event_name: str
    form_name: str
    field_name: str
    old_value: Any
    new_value: Any
    repeat_instrument: str = ""
    repeat_instance: str = ""
    change_timestamp: str = ""
    
    def __post_init__(self):
        if not self.change_timestamp:
            self.change_timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FieldChange":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ChangeSet:
    """Represents a set of changes for one upload operation."""
    operation_id: str
    timestamp: str
    file_path: str
    file_hash: str
    total_records: int
    total_changes: int
    changes: List[FieldChange]
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'operation_id': self.operation_id,
            'timestamp': self.timestamp,
            'file_path': self.file_path,
            'file_hash': self.file_hash,
            'total_records': self.total_records,
            'total_changes': self.total_changes,
            'changes': [change.to_dict() for change in self.changes]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChangeSet":
        """Create from dictionary."""
        changes = [FieldChange.from_dict(change) for change in data.get('changes', [])]
        return cls(
            operation_id=data['operation_id'],
            timestamp=data['timestamp'],
            file_path=data['file_path'],
            file_hash=data['file_hash'],
            total_records=data['total_records'],
            total_changes=data['total_changes'],
            changes=changes
        )


class ChangeTracker:
    """Track changes made during upload operations."""
    
    def __init__(self, logs_dir: Path):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        self.change_log_file = self.logs_dir / "change_tracking.json"
        self.upload_log_file = self.logs_dir / "upload_tracking.json"
        self.logger = logging.getLogger(__name__)
    
    def track_upload(self, upload_type: str, file_paths: List[str], 
                     initials: str, records_count: int) -> str:
        """
        Track an upload operation.
        
        Args:
            upload_type: Type of upload (qc_status, query_resolution)
            file_paths: List of file paths uploaded
            initials: User initials
            records_count: Number of records uploaded
            
        Returns:
            Operation ID for tracking
        """
        try:
            operation_id = f"{upload_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{initials}"
            
            upload_entry = {
                'operation_id': operation_id,
                'timestamp': datetime.now().isoformat(),
                'upload_type': upload_type,
                'file_paths': file_paths,
                'user_initials': initials,
                'records_count': records_count,
                'status': 'completed'
            }
            
            # Load existing log or create new
            upload_log = self._load_upload_log()
            upload_log['uploads'].append(upload_entry)
            
            # Save updated log
            self._save_upload_log(upload_log)
            
            self.logger.info(f"Tracked upload operation: {operation_id}")
            return operation_id
            
        except Exception as e:
            self.logger.error(f"Error tracking upload: {str(e)}")
            return ""
    
    def track_changes(self, operation_id: str, file_path: str, file_hash: str,
                     old_data: List[Dict[str, Any]], new_data: List[Dict[str, Any]]) -> ChangeSet:
        """
        Track changes between old and new data.
        
        Args:
            operation_id: Unique operation identifier
            file_path: Source file path
            file_hash: Hash of source file
            old_data: Original data from REDCap
            new_data: New data to be uploaded
            
        Returns:
            ChangeSet containing all tracked changes
        """
        try:
            changes = self._compare_data(old_data, new_data)
            
            change_set = ChangeSet(
                operation_id=operation_id,
                timestamp=datetime.now().isoformat(),
                file_path=file_path,
                file_hash=file_hash,
                total_records=len(new_data),
                total_changes=len(changes),
                changes=changes
            )
            
            # Save change set
            self._save_change_set(change_set)
            
            self.logger.info(f"Tracked {len(changes)} changes for operation {operation_id}")
            return change_set
            
        except Exception as e:
            self.logger.error(f"Error tracking changes: {str(e)}")
            return ChangeSet(operation_id, "", file_path, file_hash, 0, 0, [])
    
    def _compare_data(self, old_data: List[Dict[str, Any]], 
                     new_data: List[Dict[str, Any]]) -> List[FieldChange]:
        """Compare old and new data to find changes."""
        changes = []
        
        try:
            # Create lookup for old data
            old_lookup = {}
            for record in old_data:
                record_id = record.get('record_id')
                event_name = record.get('redcap_event_name', '')
                repeat_instrument = record.get('redcap_repeat_instrument', '')
                repeat_instance = record.get('redcap_repeat_instance', '')
                
                key = f"{record_id}|{event_name}|{repeat_instrument}|{repeat_instance}"
                old_lookup[key] = record
            
            # Compare with new data
            for new_record in new_data:
                record_id = new_record.get('record_id')
                event_name = new_record.get('redcap_event_name', '')
                repeat_instrument = new_record.get('redcap_repeat_instrument', '')
                repeat_instance = new_record.get('redcap_repeat_instance', '')
                
                key = f"{record_id}|{event_name}|{repeat_instrument}|{repeat_instance}"
                old_record = old_lookup.get(key, {})
                
                # Compare each field
                for field_name, new_value in new_record.items():
                    if field_name.startswith('redcap_'):
                        continue  # Skip REDCap system fields
                    
                    old_value = old_record.get(field_name, '')
                    
                    # Check if value changed
                    if str(old_value) != str(new_value):
                        change = FieldChange(
                            record_id=record_id,
                            event_name=event_name,
                            form_name=self._get_form_name(field_name),
                            field_name=field_name,
                            old_value=old_value,
                            new_value=new_value,
                            repeat_instrument=repeat_instrument,
                            repeat_instance=repeat_instance
                        )
                        changes.append(change)
            
        except Exception as e:
            self.logger.error(f"Error comparing data: {str(e)}")
        
        return changes
    
    def _get_form_name(self, field_name: str) -> str:
        """Get form name for a field (placeholder implementation)."""
        # This would typically use REDCap metadata to determine the form
        # For now, return a default or infer from field name
        if 'qc_' in field_name:
            return 'qc_status'
        elif 'query_' in field_name:
            return 'query_resolution'
        else:
            return 'unknown_form'
    
    def _load_upload_log(self) -> Dict[str, Any]:
        """Load upload log from disk."""
        try:
            if self.upload_log_file.exists():
                with open(self.upload_log_file, 'r') as f:
                    return json.load(f)
            else:
                return {'uploads': []}
        except Exception as e:
            self.logger.error(f"Error loading upload log: {str(e)}")
            return {'uploads': []}
    
    def _save_upload_log(self, upload_log: Dict[str, Any]) -> None:
        """Save upload log to disk."""
        try:
            with open(self.upload_log_file, 'w') as f:
                json.dump(upload_log, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving upload log: {str(e)}")
    
    def _save_change_set(self, change_set: ChangeSet) -> None:
        """Save change set to disk."""
        try:
            # Load existing change log
            change_log = self._load_change_log()
            
            # Add new change set
            change_log['change_sets'].append(change_set.to_dict())
            
            # Save updated log
            with open(self.change_log_file, 'w') as f:
                json.dump(change_log, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving change set: {str(e)}")
    
    def _load_change_log(self) -> Dict[str, Any]:
        """Load change log from disk."""
        try:
            if self.change_log_file.exists():
                with open(self.change_log_file, 'r') as f:
                    return json.load(f)
            else:
                return {'change_sets': []}
        except Exception as e:
            self.logger.error(f"Error loading change log: {str(e)}")
            return {'change_sets': []}
    
    def get_operation_history(self, operation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get upload operation history."""
        try:
            upload_log = self._load_upload_log()
            
            if operation_id:
                return [op for op in upload_log['uploads'] if op['operation_id'] == operation_id]
            else:
                return upload_log['uploads']
                
        except Exception as e:
            self.logger.error(f"Error getting operation history: {str(e)}")
            return []
    
    def get_change_history(self, operation_id: Optional[str] = None) -> List[ChangeSet]:
        """Get change history."""
        try:
            change_log = self._load_change_log()
            change_sets = []
            
            for change_data in change_log['change_sets']:
                if operation_id is None or change_data['operation_id'] == operation_id:
                    change_sets.append(ChangeSet.from_dict(change_data))
            
            return change_sets
            
        except Exception as e:
            self.logger.error(f"Error getting change history: {str(e)}")
            return []
    
    def generate_change_report(self, operation_id: str) -> Dict[str, Any]:
        """Generate a comprehensive change report for an operation."""
        try:
            upload_history = self.get_operation_history(operation_id)
            change_history = self.get_change_history(operation_id)
            
            if not upload_history:
                return {'error': f'No operation found with ID: {operation_id}'}
            
            operation = upload_history[0]
            changes = change_history[0] if change_history else None
            
            report = {
                'operation_id': operation_id,
                'operation_details': operation,
                'change_summary': {
                    'total_records': changes.total_records if changes else 0,
                    'total_changes': changes.total_changes if changes else 0,
                    'records_with_changes': len(set(c.record_id for c in changes.changes)) if changes else 0
                },
                'changes_by_form': {},
                'changes_by_field': {}
            }
            
            if changes:
                # Group changes by form
                for change in changes.changes:
                    form_name = change.form_name
                    if form_name not in report['changes_by_form']:
                        report['changes_by_form'][form_name] = 0
                    report['changes_by_form'][form_name] += 1
                
                # Group changes by field
                for change in changes.changes:
                    field_name = change.field_name
                    if field_name not in report['changes_by_field']:
                        report['changes_by_field'][field_name] = 0
                    report['changes_by_field'][field_name] += 1
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating change report: {str(e)}")
            return {'error': str(e)}
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not self.operation_id:
            self.operation_id = f"upload_{self.timestamp.replace(':', '').replace('-', '')}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'operation_id': self.operation_id,
            'timestamp': self.timestamp,
            'file_path': self.file_path,
            'file_hash': self.file_hash,
            'total_records': self.total_records,
            'total_changes': self.total_changes,
            'changes': [change.to_dict() for change in self.changes],
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChangeSet":
        """Create from dictionary."""
        changes = [FieldChange.from_dict(change) for change in data.get('changes', [])]
        return cls(
            operation_id=data['operation_id'],
            timestamp=data['timestamp'],
            file_path=data['file_path'],
            file_hash=data['file_hash'],
            total_records=data['total_records'],
            total_changes=data['total_changes'],
            changes=changes,
            metadata=data.get('metadata', {})
        )


class ChangeTracker:
    """Track and log changes between current and new data."""
    
    def __init__(self, logs_dir: Path):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Store changes for current operation
        self.current_changes: List[FieldChange] = []
        self.operation_metadata: Dict[str, Any] = {}
    
    def compare_dataframes(
        self, 
        current_df: pd.DataFrame, 
        new_df: pd.DataFrame,
        key_columns: List[str],
        form_name: str,
        exclude_columns: Optional[List[str]] = None
    ) -> List[FieldChange]:
        """Compare two dataframes and identify changes."""
        changes = []
        exclude_columns = exclude_columns or []
        
        # Ensure both dataframes have the same key columns
        missing_keys_current = set(key_columns) - set(current_df.columns)
        missing_keys_new = set(key_columns) - set(new_df.columns)
        
        if missing_keys_current or missing_keys_new:
            logger.error(f"Missing key columns - Current: {missing_keys_current}, New: {missing_keys_new}")
            return changes
        
        # Create a merged dataset to compare
        merged = pd.merge(
            current_df, 
            new_df, 
            on=key_columns, 
            how='outer', 
            suffixes=('_current', '_new'),
            indicator=True
        )
        
        # Get comparable columns (exclude keys and system columns)
        comparable_columns = []
        for col in new_df.columns:
            if (col not in key_columns and 
                col not in exclude_columns and
                not col.startswith('redcap_') and
                col + '_current' in merged.columns and
                col + '_new' in merged.columns):
                comparable_columns.append(col)
        
        logger.info(f"Comparing {len(comparable_columns)} columns across {len(merged)} records")
        
        # Iterate through merged data to find changes
        for idx, row in merged.iterrows():
            record_id = str(row.get('ptid', row.get('record_id', f'row_{idx}')))
            event_name = str(row.get('redcap_event_name', ''))
            repeat_instrument = str(row.get('redcap_repeat_instrument', ''))
            repeat_instance = str(row.get('redcap_repeat_instance', ''))
            
            for col in comparable_columns:
                current_val = row.get(f'{col}_current')
                new_val = row.get(f'{col}_new')
                
                # Check for changes (handle NaN values)
                if self._values_different(current_val, new_val):
                    change = FieldChange(
                        record_id=record_id,
                        event_name=event_name,
                        form_name=form_name,
                        field_name=col,
                        old_value=self._format_value(current_val),
                        new_value=self._format_value(new_val),
                        repeat_instrument=repeat_instrument,
                        repeat_instance=repeat_instance
                    )
                    changes.append(change)
        
        logger.info(f"Found {len(changes)} field changes for form '{form_name}'")
        return changes
    
    def _values_different(self, val1: Any, val2: Any) -> bool:
        """Check if two values are different, handling NaN cases."""
        # Handle NaN values
        if pd.isna(val1) and pd.isna(val2):
            return False
        if pd.isna(val1) or pd.isna(val2):
            return True
        
        # Convert to strings for comparison to handle type differences
        str1 = str(val1).strip() if val1 is not None else ""
        str2 = str(val2).strip() if val2 is not None else ""
        
        # Handle empty strings vs NaN
        if (str1 == "" or str1.lower() == "nan") and (str2 == "" or str2.lower() == "nan"):
            return False
        
        return str1 != str2
    
    def _format_value(self, value: Any) -> str:
        """Format value for logging."""
        if pd.isna(value) or value is None:
            return ""
        return str(value).strip()
    
    def add_changes(self, changes: List[FieldChange]) -> None:
        """Add changes to current operation."""
        self.current_changes.extend(changes)
        logger.info(f"Added {len(changes)} changes to current operation")
    
    def set_operation_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set metadata for current operation."""
        self.operation_metadata.update(metadata)
    
    def create_changeset(
        self, 
        file_path: str, 
        file_hash: str, 
        total_records: int,
        operation_id: Optional[str] = None
    ) -> ChangeSet:
        """Create a changeset from current changes."""
        changeset = ChangeSet(
            operation_id=operation_id or "",
            timestamp="",  # Will be set in __post_init__
            file_path=file_path,
            file_hash=file_hash,
            total_records=total_records,
            total_changes=len(self.current_changes),
            changes=self.current_changes.copy(),
            metadata=self.operation_metadata.copy()
        )
        
        return changeset
    
    def save_changeset(self, changeset: ChangeSet) -> Path:
        """Save changeset to audit log file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.logs_dir / f"audit_{timestamp}.json"
        
        try:
            with open(log_file, 'w') as f:
                json.dump(changeset.to_dict(), f, indent=2, default=str)
            
            logger.info(f"Saved audit log: {log_file}")
            return log_file
            
        except Exception as e:
            logger.error(f"Error saving audit log: {e}")
            raise
    
    def save_summary_report(self, changeset: ChangeSet) -> Path:
        """Save human-readable summary report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = self.logs_dir / f"summary_{timestamp}.txt"
        
        try:
            with open(summary_file, 'w') as f:
                f.write("REDCap Data Upload Summary\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"Operation ID: {changeset.operation_id}\n")
                f.write(f"Timestamp: {changeset.timestamp}\n")
                f.write(f"Source File: {changeset.file_path}\n")
                f.write(f"File Hash: {changeset.file_hash}\n")
                f.write(f"Total Records: {changeset.total_records}\n")
                f.write(f"Total Changes: {changeset.total_changes}\n\n")
                
                # Metadata
                if changeset.metadata:
                    f.write("Metadata:\n")
                    for key, value in changeset.metadata.items():
                        f.write(f"  {key}: {value}\n")
                    f.write("\n")
                
                # Summary by form
                form_summary = {}
                for change in changeset.changes:
                    form = change.form_name
                    if form not in form_summary:
                        form_summary[form] = {'total': 0, 'fields': set()}
                    form_summary[form]['total'] += 1
                    form_summary[form]['fields'].add(change.field_name)
                
                f.write("Changes by Form:\n")
                for form, info in form_summary.items():
                    f.write(f"  {form}: {info['total']} changes across {len(info['fields'])} fields\n")
                    for field in sorted(info['fields']):
                        field_changes = [c for c in changeset.changes if c.form_name == form and c.field_name == field]
                        f.write(f"    - {field}: {len(field_changes)} changes\n")
                f.write("\n")
                
                # Detailed changes (first 100)
                f.write("Detailed Changes (first 100):\n")
                f.write("-" * 50 + "\n")
                
                for i, change in enumerate(changeset.changes[:100]):
                    f.write(f"{i+1}. Record {change.record_id}")
                    if change.event_name:
                        f.write(f" | Event: {change.event_name}")
                    if change.repeat_instrument:
                        f.write(f" | Repeat: {change.repeat_instrument}#{change.repeat_instance}")
                    f.write(f"\n   Form: {change.form_name} | Field: {change.field_name}\n")
                    f.write(f"   Old: '{change.old_value}' → New: '{change.new_value}'\n\n")
                
                if len(changeset.changes) > 100:
                    f.write(f"... and {len(changeset.changes) - 100} more changes\n")
            
            logger.info(f"Saved summary report: {summary_file}")
            return summary_file
            
        except Exception as e:
            logger.error(f"Error saving summary report: {e}")
            raise
    
    def save_backup_data(self, data: pd.DataFrame, operation_id: str) -> Path:
        """Save backup of original data."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.logs_dir.parent / "backups" / f"backup_{timestamp}.json"
        
        # Ensure backup directory exists
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Convert DataFrame to JSON
            backup_data = {
                'operation_id': operation_id,
                'timestamp': timestamp,
                'data': data.to_dict('records')
            }
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            logger.info(f"Saved data backup: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"Error saving backup data: {e}")
            raise
    
    def clear_current_changes(self) -> None:
        """Clear current changes and metadata."""
        self.current_changes.clear()
        self.operation_metadata.clear()
    
    def get_change_statistics(self) -> Dict[str, Any]:
        """Get statistics about current changes."""
        if not self.current_changes:
            return {'total_changes': 0}
        
        stats = {
            'total_changes': len(self.current_changes),
            'unique_records': len(set(c.record_id for c in self.current_changes)),
            'unique_forms': len(set(c.form_name for c in self.current_changes)),
            'unique_fields': len(set(c.field_name for c in self.current_changes)),
            'changes_by_form': {},
            'changes_by_field': {}
        }
        
        # Count by form
        for change in self.current_changes:
            form = change.form_name
            field = change.field_name
            
            if form not in stats['changes_by_form']:
                stats['changes_by_form'][form] = 0
            stats['changes_by_form'][form] += 1
            
            if field not in stats['changes_by_field']:
                stats['changes_by_field'][field] = 0
            stats['changes_by_field'][field] += 1
        
        return stats
