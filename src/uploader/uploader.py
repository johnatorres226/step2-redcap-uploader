"""Data upload functionality for REDCap."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from ..config.redcap_config import REDCapConfig
from ..config.settings import Settings
from .change_tracker import ChangeTracker
from .data_processor import DataProcessor
from .fetcher import REDCapFetcher
from .file_monitor import FileMonitor

logger = logging.getLogger(__name__)


class QCDataUploader:
    """Main uploader class for handling QC Status and Query Resolution uploads."""
    
    def __init__(self, config: REDCapConfig, settings: Settings, logger: logging.Logger):
        self.config = config
        self.settings = settings
        self.logger = logger
        self.session = requests.Session()
        
        # Initialize components
        self.fetcher = REDCapFetcher(config, logger)
        self.data_processor = DataProcessor(strict_validation=False)
        self.change_tracker = ChangeTracker(settings.LOGS_DIR)
        self.file_monitor = FileMonitor(Path(settings.UPLOAD_READY_PATH), logger)
    
    def upload_qc_status_data(self, upload_path: Optional[Path] = None, 
                            specific_file: Optional[Path] = None,
                            initials: str = "", 
                            dry_run: bool = False, force_upload: bool = False,
                            custom_output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Upload QC Status Report Data from JSON files.
        
        Args:
            upload_path: Path to directory containing JSON files (deprecated - use specific_file)
            specific_file: Path to specific JSON file to upload
            initials: User initials for logging
            dry_run: If True, perform validation without actual upload
            force_upload: If True, skip duplicate checking
            custom_output_dir: If provided, use this directory instead of creating a new one
            
        Returns:
            Dict containing upload results
        """
        try:
            self.logger.info(f"Starting QC Status upload process (User: {initials})")

            # Create output directory
            if custom_output_dir:
                output_dir = custom_output_dir
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = self._create_output_directory("QC_STATUS")
                
            # Determine which files to process
            json_files = []
            if specific_file:
                # Process only the specific file
                if not specific_file.exists():
                    return {
                        'success': False,
                        'error': f'Specified file not found: {specific_file}',
                        'output_directory': str(output_dir)
                    }
                json_files = [specific_file]
                self.logger.info(f"Processing specific file: {specific_file.name}")
            elif upload_path:
                # Fall back to old behavior for backward compatibility
                json_files = self._find_latest_files(upload_path, "*.json")
                self.logger.warning("Using deprecated upload_path parameter. Consider using specific_file instead.")
            else:
                return {
                    'success': False,
                    'error': 'Either specific_file or upload_path must be provided',
                    'output_directory': str(output_dir)
                }
            
            if not json_files:
                error_msg = 'No JSON files found'
                if upload_path:
                    error_msg += f' in {upload_path}'
                return {
                    'success': False,
                    'error': error_msg,
                    'output_directory': str(output_dir)
                }
            
            # Get current data from REDCap for comparison
            current_data_result = self.fetcher.fetch_qc_status_data()
            if not current_data_result['success']:
                return {
                    'success': False,
                    'error': f"Failed to fetch current data: {current_data_result['error']}",
                    'output_directory': str(output_dir)
                }
            
            current_data = current_data_result['data']
            
            # Process each JSON file
            total_processed = 0
            upload_data = []
            
            for json_file in json_files:
                self.logger.info(f"Processing file: {json_file.name}")
                
                # Load file
                file_result = self._load_json_file(json_file)
                if not file_result['success']:
                    self.logger.error(f"Failed to load {json_file.name}: {file_result['error']}")
                    continue
                
                file_data = file_result['data']
                
                # Validate data
                validation_result = self._validate_qc_data(file_data)
                if not validation_result['is_valid']:
                    self.logger.error(f"Validation failed for {json_file.name}")
                    continue
                
                # Check for duplicates (unless forced)
                if not force_upload:
                    new_records = self._filter_new_records(file_data, current_data)
                    if not new_records:
                        self.logger.info(f"No new records to upload from {json_file.name}")
                        continue
                    upload_data.extend(new_records)
                else:
                    upload_data.extend(file_data)
                
                total_processed += len(file_data)
            
            if not upload_data:
                return {
                    'success': True,
                    'message': 'No new records to upload',
                    'records_processed': 0,
                    'output_directory': str(output_dir)
                }
            
            # Add audit trail to upload data
            self.logger.info("Adding audit trail entries to upload data...")
            upload_data_with_audit = self.data_processor.add_audit_trail(
                upload_data, current_data, initials
            )

            # Create backup data for upload receipt
            backup_data = self._create_backup_data(current_data, upload_data_with_audit)

            # Perform upload (if not dry run)
            if not dry_run:
                upload_result = self._upload_to_redcap(upload_data_with_audit)
                
                if upload_result['success']:
                    # Create upload receipt
                    receipt_data = {
                        'upload_timestamp': datetime.now().isoformat(),
                        'user_initials': initials,
                        'records_uploaded': len(upload_data_with_audit),
                        'files_processed': [f.name for f in json_files],
                        'upload_result': upload_result
                    }
                    
                    receipt_file = output_dir / f"DataUploaded_Recipt_{datetime.now().strftime('%d%b%Y_%H%M%S')}.json"
                    with open(receipt_file, 'w', encoding='utf-8') as f:
                        json.dump(receipt_data, f, indent=2, ensure_ascii=False)
                    
                    # Save uploaded data to file for reference
                    uploaded_data_file = output_dir / f"DataUploaded_{datetime.now().strftime('%d%b%Y_%H%M%S')}.json"
                    with open(uploaded_data_file, 'w', encoding='utf-8') as f:
                        json.dump(upload_data_with_audit, f, indent=2, ensure_ascii=False)
                    
                    # Update tracking
                    self._track_upload(
                        upload_type='qc_status',
                        file_paths=[str(f) for f in json_files],
                        initials=initials,
                        records_count=len(upload_data_with_audit)
                    )
                    
                    self.logger.info(f"Successfully uploaded {len(upload_data_with_audit)} QC Status records")
                    
                    return {
                        'success': True,
                        'records_processed': len(upload_data_with_audit),
                        'output_directory': str(output_dir),
                        'receipt_file': str(receipt_file),
                        'uploaded_data_file': str(uploaded_data_file),
                        'backup_data': backup_data
                    }
                else:
                    return {
                        'success': False,
                        'error': upload_result['error'],
                        'output_directory': str(output_dir)
                    }
            else:
                self.logger.info(f"DRY RUN: Would upload {len(upload_data_with_audit)} records")
                return {
                    'success': True,
                    'records_processed': len(upload_data_with_audit),
                    'output_directory': str(output_dir),
                    'dry_run': True
                }
                
        except Exception as e:
            error_msg = f"Error in QC Status upload: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def upload_query_resolution_data(self, data_file: Path, initials: str, 
                                   dry_run: bool = False) -> Dict[str, Any]:
        """
        Upload Query Resolution Data from CSV/Excel file.
        
        Args:
            data_file: Path to CSV or Excel file
            initials: User initials for logging
            dry_run: If True, perform validation without actual upload
            
        Returns:
            Dict containing upload results
        """
        try:
            self.logger.info(f"Starting Query Resolution upload process (User: {initials})")
            
            # Create output directory
            output_dir = self._create_output_directory("QUERY_RESOLUTION")
            
            # Load data file
            if data_file.suffix.lower() in ['.csv']:
                file_result = self._load_csv_file(data_file)
            elif data_file.suffix.lower() in ['.xlsx', '.xls']:
                file_result = self._load_excel_file(data_file)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported file format: {data_file.suffix}',
                    'output_directory': str(output_dir)
                }
            
            if not file_result['success']:
                return {
                    'success': False,
                    'error': file_result['error'],
                    'output_directory': str(output_dir)
                }
            
            upload_data = file_result['data']
            
            # Convert to REDCap format
            upload_data = self._convert_to_redcap_format(upload_data)
            
            # Get current data for backup
            current_data_result = self.fetcher.fetch_qc_status_data()
            current_data = current_data_result.get('data', []) if current_data_result['success'] else []
            
            # Create fallback file
            fallback_data = self._create_backup_data(current_data, upload_data)
            fallback_file = output_dir / f"FALLBACK_FILE_{datetime.now().strftime('%d%b%Y_%H%M%S')}.json"
            with open(fallback_file, 'w', encoding='utf-8') as f:
                json.dump(fallback_data, f, indent=2, ensure_ascii=False)
            
            # Perform upload (if not dry run)
            if not dry_run:
                upload_result = self._upload_to_redcap(upload_data)
                
                if upload_result['success']:
                    # Create upload receipt
                    receipt_data = {
                        'upload_timestamp': datetime.now().isoformat(),
                        'user_initials': initials,
                        'records_uploaded': len(upload_data),
                        'source_file': str(data_file),
                        'upload_result': upload_result
                    }
                    
                    receipt_file = output_dir / f"DATA_UPLOAD_RECEIPT_{datetime.now().strftime('%d%b%Y_%H%M%S')}.json"
                    with open(receipt_file, 'w', encoding='utf-8') as f:
                        json.dump(receipt_data, f, indent=2, ensure_ascii=False)
                    
                    # Update tracking
                    self._track_upload(
                        upload_type='query_resolution',
                        file_paths=[str(data_file)],
                        initials=initials,
                        records_count=len(upload_data)
                    )
                    
                    self.logger.info(f"Successfully uploaded {len(upload_data)} Query Resolution records")
                    
                    return {
                        'success': True,
                        'records_processed': len(upload_data),
                        'output_directory': str(output_dir),
                        'fallback_file': str(fallback_file),
                        'receipt_file': str(receipt_file)
                    }
                else:
                    return {
                        'success': False,
                        'error': upload_result['error'],
                        'output_directory': str(output_dir)
                    }
            else:
                self.logger.info(f"DRY RUN: Would upload {len(upload_data)} records")
                return {
                    'success': True,
                    'records_processed': len(upload_data),
                    'output_directory': str(output_dir),
                    'dry_run': True
                }
                
        except Exception as e:
            error_msg = f"Error in Query Resolution upload: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _create_output_directory(self, upload_type: str) -> Path:
        """Create output directory with timestamp."""
        timestamp = datetime.now().strftime('%d%b%Y')
        dir_name = f"REDCAP_UPLOADER_{upload_type}_{timestamp}"
        output_dir = Path('./output') / dir_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file
        log_file = output_dir / "LOG_FILE.txt"
        if not log_file.exists():
            with open(log_file, 'w') as f:
                f.write(f"Upload Log - Created: {datetime.now().isoformat()}\n")
                f.write("="*50 + "\n\n")
        
        return output_dir
    
    def _find_latest_files(self, directory: Path, pattern: str = "*.json") -> List[Path]:
        """Find the latest files in a directory matching a pattern."""
        try:
            files = list(directory.glob(pattern))
            # Sort by modification time, newest first
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            self.logger.info(f"Found {len(files)} files matching pattern '{pattern}' in {directory}")
            return files
            
        except Exception as e:
            self.logger.error(f"Error finding files in {directory}: {str(e)}")
            return []
    
    def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Load and validate JSON file."""
        try:
            self.logger.info(f"Loading JSON file: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate structure
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict) and 'data' in data:
                records = data['data']
            else:
                records = [data] if data else []
            
            self.logger.info(f"Loaded {len(records)} records from {file_path.name}")
            
            return {
                'success': True,
                'data': records,
                'file_path': str(file_path),
                'record_count': len(records)
            }
            
        except Exception as e:
            error_msg = f"Error loading file {file_path}: {str(e)}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def _load_csv_file(self, file_path: Path) -> Dict[str, Any]:
        """Load and process CSV file."""
        try:
            self.logger.info(f"Loading CSV file: {file_path}")
            
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Convert to records format
            records = df.to_dict('records')
            
            self.logger.info(f"Loaded {len(records)} records from {file_path.name}")
            
            return {
                'success': True,
                'data': records,
                'file_path': str(file_path),
                'record_count': len(records)
            }
            
        except Exception as e:
            error_msg = f"Error loading CSV file {file_path}: {str(e)}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def _load_excel_file(self, file_path: Path, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """Load and process Excel file."""
        try:
            self.logger.info(f"Loading Excel file: {file_path}")
            
            # Read Excel file
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(file_path)
            
            # Convert to records format
            records = df.to_dict('records')
            
            self.logger.info(f"Loaded {len(records)} records from {file_path.name}")
            
            return {
                'success': True,
                'data': records,
                'file_path': str(file_path),
                'record_count': len(records)
            }
            
        except Exception as e:
            error_msg = f"Error loading Excel file {file_path}: {str(e)}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def _validate_qc_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate QC Status data structure and content."""
        try:
            validation_errors = []
            required_fields = ['ptid', 'qc_last_run']
            
            for i, record in enumerate(data):
                record_errors = []
                
                # Check required fields
                for field in required_fields:
                    if field not in record or not record[field]:
                        record_errors.append(f"Missing required field: {field}")
                
                if record_errors:
                    validation_errors.append({
                        'record_index': i,
                        'record_id': record.get('ptid', 'Unknown'),
                        'errors': record_errors
                    })
            
            is_valid = len(validation_errors) == 0
            
            return {
                'is_valid': is_valid,
                'total_records': len(data),
                'error_count': len(validation_errors),
                'validation_errors': validation_errors
            }
            
        except Exception as e:
            return {
                'is_valid': False,
                'error': str(e)
            }
    
    def _convert_to_redcap_format(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert data to REDCap import format."""
        try:
            converted_data = []
            
            for record in data:
                # Ensure all values are strings (REDCap requirement)
                converted_record = {}
                for key, value in record.items():
                    if value is None:
                        converted_record[key] = ''
                    elif isinstance(value, (int, float)):
                        converted_record[key] = str(value)
                    elif isinstance(value, bool):
                        converted_record[key] = '1' if value else '0'
                    else:
                        converted_record[key] = str(value)
                
                converted_data.append(converted_record)
            
            self.logger.info(f"Converted {len(converted_data)} records to REDCap format")
            return converted_data
            
        except Exception as e:
            self.logger.error(f"Error converting data to REDCap format: {str(e)}")
            raise
    
    def _create_backup_data(self, original_data: List[Dict[str, Any]], 
                          new_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create backup data structure for fallback purposes."""
        try:
            backup_data = {
                'backup_timestamp': datetime.now().isoformat(),
                'original_data': original_data,
                'new_data': new_data,
                'original_record_count': len(original_data),
                'new_record_count': len(new_data),
                'backup_metadata': {
                    'created_by': 'QCDataUploader',
                    'purpose': 'Fallback for data upload'
                }
            }
            
            self.logger.info(f"Created backup data with {len(original_data)} original and {len(new_data)} new records")
            return backup_data
            
        except Exception as e:
            self.logger.error(f"Error creating backup data: {str(e)}")
            raise
    
    def _filter_new_records(self, new_data: List[Dict[str, Any]], 
                          current_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out records that have already been uploaded based on qc_last_run."""
        if not current_data:
            return new_data
        
        # Create lookup of current qc_last_run values by ptid
        current_lookup = {}
        for record in current_data:
            record_id = record.get('ptid')
            qc_last_run = record.get('qc_last_run')
            if record_id and qc_last_run:
                current_lookup[record_id] = qc_last_run
        
        # Filter new records
        new_records = []
        for record in new_data:
            record_id = record.get('ptid')
            qc_last_run = record.get('qc_last_run')
            
            if record_id and qc_last_run:
                current_qc_last_run = current_lookup.get(record_id)
                
                # Upload if record is new or qc_last_run has changed
                if not current_qc_last_run or current_qc_last_run != qc_last_run:
                    new_records.append(record)
                else:
                    self.logger.debug(f"Skipping record {record_id} - already uploaded")
        
        self.logger.info(f"Filtered {len(new_data)} records down to {len(new_records)} new records")
        return new_records
    
    def _upload_to_redcap(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Upload data to REDCap via API using import specification from REDCAP_IMPORT_EXPORT.md.
        
        Following the REDCap API Import Records specification:
        - content: record
        - format: json
        - type: flat (one record per row)
        - overwriteBehavior: overwrite (blank/empty values are valid and will overwrite data)
        - forceAutoNumber: false (use provided record names)
        - returnContent: count (return number of records imported)
        - returnFormat: json
        """
        try:
            self.logger.info(f"Uploading {len(data)} records to REDCap using flat JSON format")
            
            # Prepare request data according to REDCap API Import Records specification
            request_data = {
                'token': self.config.api_token,
                'content': 'record',
                'format': 'json',
                'type': 'flat',  # Output as one record per row
                'overwriteBehavior': 'overwrite',  # Blank/empty values will overwrite data
                'forceAutoNumber': 'false',  # Use provided record names
                'data': json.dumps(data),  # JSON formatted data
                'returnContent': 'count',  # Return number of records imported
                'returnFormat': 'json'  # Return response as JSON
            }
            
            self.logger.debug(f"REDCap API request parameters: {list(request_data.keys())}")
            self.logger.debug(f"Uploading to URL: {self.config.api_url}")
            
            # Make API request
            response = self.session.post(
                self.config.api_url,
                data=request_data,
                timeout=self.config.timeout
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse response - should be JSON with count
            try:
                result = response.json()
                
                # REDCap returns count as either an integer or a dict with 'count' key
                if isinstance(result, dict):
                    imported_count = result.get('count', 0)
                else:
                    imported_count = int(result) if str(result).isdigit() else 0
                
                self.logger.info(f"Upload completed successfully: {imported_count} records imported")
                
                return {
                    'success': True,
                    'records_imported': imported_count,
                    'redcap_response': result,
                    'total_sent': len(data)
                }
                
            except (json.JSONDecodeError, ValueError):
                # Handle non-JSON response
                response_text = response.text
                self.logger.warning(f"Non-JSON response from REDCap: {response_text}")
                
                # Try to extract count from text response
                if response_text.isdigit():
                    imported_count = int(response_text)
                    self.logger.info(f"Upload completed: {imported_count} records imported")
                    return {
                        'success': True,
                        'records_imported': imported_count,
                        'redcap_response': response_text,
                        'total_sent': len(data)
                    }
                else:
                    return {
                        'success': False,
                        'error': f"Could not parse REDCap response: {response_text}",
                        'response_text': response_text
                    }
            
        except requests.exceptions.Timeout as e:
            error_msg = f"REDCap API request timed out after {self.config.timeout} seconds: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'timeout'
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"REDCap API request failed: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f" Response: {e.response.text}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'request_failed'
            }
            
        except Exception as e:
            error_msg = f"Unexpected error during upload: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'unexpected'
            }
    
    def _track_upload(self, upload_type: str, file_paths: List[str], 
                     initials: str, records_count: int) -> None:
        """Track upload in comprehensive log."""
        try:
            # Create tracking entry
            tracking_entry = {
                'timestamp': datetime.now().isoformat(),
                'upload_type': upload_type,
                'file_paths': file_paths,
                'user_initials': initials,
                'records_count': records_count
            }
            
            # Write to comprehensive log
            log_file = self.settings.LOGS_DIR / "comprehensive_upload_log.json"
            
            # Load existing log or create new
            if log_file.exists():
                with open(log_file, 'r') as f:
                    log_data = json.load(f)
            else:
                log_data = {'uploads': []}
            
            log_data['uploads'].append(tracking_entry)
            
            # Save updated log
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            # Also create backup at BACKUP_LOG_PATH if specified
            backup_path = self.settings.BACKUPS_DIR / "comprehensive_upload_log_backup.json"
            with open(backup_path, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            self.logger.info(f"Upload tracked successfully: {upload_type}")
            
        except Exception as e:
            self.logger.error(f"Error tracking upload: {str(e)}")
