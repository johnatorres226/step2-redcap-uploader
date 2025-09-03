"""REDCap data fetching module."""

import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..config.redcap_config import REDCapConfig


class REDCapFetcher:
    """Handles fetching data from REDCap API."""
    
    def __init__(self, config: REDCapConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.session = requests.Session()
        
        # QC STATUS form fields that we typically work with
        self.qc_status_fields = [
            'ptid',
            'qc_status_complete',
            'qc_visit_date',
            'qc_last_run',
            'qc_notes',
            'qc_status',
            'qc_results',
            'qc_run_by',
            'quality_control_check_complete'
        ]
    
    def analyze_upload_data(self, upload_path: Path) -> Dict[str, Any]:
        """
        Analyze upload data to determine what fields and records we need to fetch.
        
        Args:
            upload_path: Path to directory containing JSON files to upload
            
        Returns:
            Dict containing analysis results
        """
        try:
            self.logger.info(f"Analyzing upload data in: {upload_path}")
            
            json_files = list(upload_path.glob("*.json"))
            if not json_files:
                return {
                    'success': False,
                    'error': 'No JSON files found in upload path',
                    'files_analyzed': 0
                }
            
            all_fields = set()
            all_record_ids = set()
            all_qc_last_runs = set()
            file_analysis = []
            
            for json_file in json_files:
                self.logger.info(f"Analyzing file: {json_file.name}")
                
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                    
                    # Handle different JSON structures
                    if isinstance(file_data, list):
                        records = file_data
                    elif isinstance(file_data, dict) and 'data' in file_data:
                        records = file_data['data']
                    else:
                        records = [file_data] if file_data else []
                    
                    file_fields = set()
                    file_record_ids = set()
                    file_qc_runs = set()
                    
                    for record in records:
                        if isinstance(record, dict):
                            # Collect all fields
                            file_fields.update(record.keys())
                            all_fields.update(record.keys())
                            
                            # Collect record IDs (check both record_id and ptid)
                            record_id = None
                            if 'record_id' in record:
                                record_id = str(record['record_id'])
                            elif 'ptid' in record:
                                record_id = str(record['ptid'])
                            
                            if record_id:
                                file_record_ids.add(record_id)
                                all_record_ids.add(record_id)
                            
                            # Collect qc_last_run values
                            if 'qc_last_run' in record and record['qc_last_run']:
                                file_qc_runs.add(str(record['qc_last_run']))
                                all_qc_last_runs.add(str(record['qc_last_run']))
                    
                    file_analysis.append({
                        'file': json_file.name,
                        'record_count': len(records),
                        'fields': list(file_fields),
                        'record_ids': list(file_record_ids),
                        'qc_last_runs': list(file_qc_runs)
                    })
                    
                    self.logger.info(f"  - Records: {len(records)}")
                    self.logger.info(f"  - Fields: {len(file_fields)}")
                    self.logger.info(f"  - Record IDs: {len(file_record_ids)}")
                    
                except Exception as e:
                    self.logger.error(f"Error analyzing file {json_file.name}: {str(e)}")
                    continue
            
            # Determine QC STATUS specific fields from the upload data
            # Filter to only QC status fields found in the upload data, excluding system fields
            qc_fields_in_upload = [field for field in all_fields 
                                 if field in self.qc_status_fields and field != 'redcap_event_name']
            
            analysis_result = {
                'success': True,
                'files_analyzed': len(json_files),
                'total_records': len(all_record_ids),
                'all_fields': list(all_fields),
                'qc_status_fields': qc_fields_in_upload,
                'record_ids': list(all_record_ids),
                'qc_last_runs': list(all_qc_last_runs),
                'file_details': file_analysis,
                'recommended_fetch_strategy': {
                    'full_backup': 'Fetch all data for backup',
                    'targeted_qc': f'Fetch QC STATUS form with fields: {qc_fields_in_upload}',
                    'specific_records': f'Focus on {len(all_record_ids)} specific record IDs'
                }
            }
            
            self.logger.info(f"Analysis complete:")
            self.logger.info(f"  - Files processed: {len(json_files)}")
            self.logger.info(f"  - Total unique records: {len(all_record_ids)}")
            self.logger.info(f"  - QC fields to fetch: {qc_fields_in_upload}")
            
            return analysis_result
            
        except Exception as e:
            error_msg = f"Error analyzing upload data: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'files_analyzed': 0
            }
    
    def fetch_complete_backup_data(self) -> Dict[str, Any]:
        """
        Fetch complete REDCap data for backup purposes.
        
        Returns:
            Dict containing all project data
        """
        try:
            self.logger.info("Fetching complete REDCap data for backup...")
            
            # Fetch ALL data without any filters
            data = {
                'token': self.config.api_token,
                'content': 'record',
                'action': 'export',
                'format': 'json',
                'type': 'flat',
                'csvDelimiter': '',
                'rawOrLabel': 'raw',
                'rawOrLabelHeaders': 'raw',
                'exportCheckboxLabel': 'false',
                'exportSurveyFields': 'false',
                'exportDataAccessGroups': 'false',
                'returnFormat': 'json'
            }
            
            response = self.session.post(
                self.config.api_url,
                data=data,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            fetched_data = response.json()
            
            self.logger.info(f"Successfully fetched complete backup data: {len(fetched_data)} records")
            
            return {
                'success': True,
                'data': fetched_data,
                'record_count': len(fetched_data),
                'fetch_timestamp': datetime.now().isoformat(),
                'fetch_type': 'complete_backup'
            }
            
        except Exception as e:
            error_msg = f"Error fetching complete backup data: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'data': None
            }
    
    def fetch_qc_status_form_data(self, record_ids: Optional[List[str]] = None, 
                                qc_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Fetch targeted QC STATUS form data for the specific records that will be updated.
        
        Args:
            record_ids: List of specific record IDs to fetch
            qc_fields: List of QC status fields to fetch
            
        Returns:
            Dict containing targeted QC STATUS data
        """
        try:
            self.logger.info("Fetching targeted QC STATUS fields data...")
            
            # Use provided fields or default QC status fields
            fields_to_fetch = qc_fields or self.qc_status_fields
            
            # Prepare request data for QC STATUS fields (without specifying form)
            data = {
                'token': self.config.api_token,
                'content': 'record',
                'action': 'export',
                'format': 'json',
                'type': 'flat',
                'csvDelimiter': '',
                'rawOrLabel': 'raw',
                'rawOrLabelHeaders': 'raw',
                'exportCheckboxLabel': 'false',
                'exportSurveyFields': 'false',
                'exportDataAccessGroups': 'false',
                'returnFormat': 'json',
                'fields': ','.join(fields_to_fetch)  # Only fetch QC-related fields
            }
            
            # Add specific record IDs if provided
            if record_ids:
                data['records'] = ','.join(record_ids)
                self.logger.info(f"Fetching QC fields for {len(record_ids)} specific records")
            
            response = self.session.post(
                self.config.api_url,
                data=data,
                timeout=self.config.timeout
            )
            
            # Check response status and log details for debugging
            if not response.ok:
                error_details = f"Status: {response.status_code}, Response: {response.text[:500]}"
                self.logger.error(f"REDCap API Error: {error_details}")
                self.logger.error(f"Request data: {data}")
            
            response.raise_for_status()
            
            fetched_data = response.json()
            
            self.logger.info(f"Successfully fetched QC STATUS fields data: {len(fetched_data)} records")
            self.logger.info(f"Fields fetched: {fields_to_fetch}")
            
            return {
                'success': True,
                'data': fetched_data,
                'record_count': len(fetched_data),
                'fields_fetched': fields_to_fetch,
                'fetch_timestamp': datetime.now().isoformat(),
                'fetch_type': 'qc_status_fields_targeted',
                'target_records': record_ids or 'all'
            }
            
        except Exception as e:
            error_msg = f"Error fetching QC STATUS fields data: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'data': None
            }
            return {
                'success': False,
                'error': error_msg,
                'data': None
            }
    
    def fetch_for_upload(self, upload_path: Path) -> Dict[str, Any]:
        """
        Perform fetching based on upload data analysis.
        This method combines analysis of upload data with targeted fetching.
        
        Args:
            upload_path: Path to directory containing JSON files to upload
            
        Returns:
            Dict containing both complete backup and targeted QC data
        """
        try:
            self.logger.info("Starting fetch process...")
            
            # Step 1: Analyze the upload data
            analysis = self.analyze_upload_data(upload_path)
            if not analysis['success']:
                return analysis

            # Step 2: Fetch complete backup data
            self.logger.info("Step 1: Fetching complete backup data...")
            backup_result = self.fetch_complete_backup_data()

            # Step 3: Fetch targeted QC STATUS data
            self.logger.info("Step 2: Fetching targeted QC STATUS data...")
            qc_result = self.fetch_qc_status_form_data(
                record_ids=analysis.get('record_ids'),
                qc_fields=analysis.get('qc_status_fields')
            )            # Combine results
            return {
                'success': True,
                'analysis': analysis,
                'complete_backup': backup_result,
                'qc_status_data': qc_result,
                'fetch_summary': {
                    'files_analyzed': analysis.get('files_analyzed', 0),
                    'records_to_update': len(analysis.get('record_ids', [])),
                    'backup_records': backup_result.get('record_count', 0) if backup_result['success'] else 0,
                    'qc_records': qc_result.get('record_count', 0) if qc_result['success'] else 0,
                    'qc_fields': qc_result.get('fields_fetched', []) if qc_result['success'] else []
                }
            }
            
        except Exception as e:
            error_msg = f"Error in fetch process: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def fetch_qc_status_data(self, records: Optional[List[str]] = None, 
                           specific_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Fetch QC Status data from REDCap.
        
        Args:
            records: Optional list of record IDs to fetch. If None, fetches all records.
            specific_fields: Optional list of field names to fetch.
            
        Returns:
            Dict containing fetched data and metadata
        """
        try:
            self.logger.info("Fetching QC Status data from REDCap")
            
            # Prepare request data according to REDCap API documentation
            data = {
                'token': self.config.api_token,
                'content': 'record',
                'action': 'export',
                'format': 'json',  # Using JSON format as specified
                'type': 'flat',    # Flat format - one record per row
                'csvDelimiter': '',
                'rawOrLabel': 'raw',  # Get raw values for processing
                'rawOrLabelHeaders': 'raw',
                'exportCheckboxLabel': 'false',
                'exportSurveyFields': 'false',
                'exportDataAccessGroups': 'false',
                'returnFormat': 'json'
            }
            
            # Add specific records if provided
            if records:
                data['records'] = ','.join(records)
                
            # Add specific fields if provided (QC status fields)
            if specific_fields:
                data['fields'] = ','.join(specific_fields)
            
            # Add specific records if provided
            if records:
                data['records'] = ','.join(records)
            
            # Make API request
            response = self.session.post(
                self.config.api_url,
                data=data,
                timeout=self.config.timeout
            )
            
            # Check response status and log details for debugging
            if not response.ok:
                error_details = f"Status: {response.status_code}, Response: {response.text[:500]}"
                self.logger.error(f"REDCap API Error: {error_details}")
                self.logger.error(f"Request data: {data}")
            
            response.raise_for_status()

            # Parse response
            fetched_data = response.json()

            self.logger.info(f"Successfully fetched {len(fetched_data)} records")

            return {
                'success': True,
                'data': fetched_data,
                'record_count': len(fetched_data),
                'fetch_timestamp': datetime.now().isoformat()
            }

        except requests.exceptions.RequestException as e:
            error_msg = f"REDCap API request failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'data': None
            }
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse REDCap response: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'data': None
            }
        except Exception as e:
            error_msg = f"Unexpected error fetching data: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'data': None
            }
    
    def export_qc_status_data(self, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Export QC Status data to JSON file.
        
        Args:
            output_dir: Directory to save exported data
            
        Returns:
            Dict containing export results
        """
        try:
            # Fetch data
            fetch_result = self.fetch_qc_status_data()
            
            if not fetch_result['success']:
                return fetch_result
            
            # Prepare output directory
            if not output_dir:
                output_dir = Path('./exports')
            output_dir.mkdir(exist_ok=True)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime('%d%b%Y_%H%M%S')
            filename = f"QC_STATUS_EXPORT_{timestamp}.json"
            file_path = output_dir / filename
            
            # Save data to file
            export_data = {
                'export_metadata': {
                    'export_timestamp': fetch_result['fetch_timestamp'],
                    'record_count': fetch_result['record_count'],
                    'exported_by': 'REDCap_Fetcher'
                },
                'data': fetch_result['data']
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Data exported to: {file_path}")
            
            return {
                'success': True,
                'file_path': str(file_path),
                'record_count': fetch_result['record_count']
            }
            
        except Exception as e:
            error_msg = f"Failed to export data: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def get_records_with_qc_last_run(self, qc_last_run_values: List[str]) -> Dict[str, Any]:
        """
        Fetch records that match specific qc_last_run values for duplicate detection.
        
        Args:
            qc_last_run_values: List of qc_last_run values to check
            
        Returns:
            Dict containing matching records
        """
        try:
            self.logger.info(f"Checking for existing records with qc_last_run values: {qc_last_run_values}")
            
            # Fetch records with qc_last_run field specifically
            result = self.fetch_qc_status_data(
                specific_fields=['record_id', 'qc_last_run']
            )
            
            if not result['success']:
                return result
            
            # Filter records that match the qc_last_run values
            matching_records = []
            for record in result['data']:
                if record.get('qc_last_run') in qc_last_run_values:
                    matching_records.append(record)
            
            self.logger.info(f"Found {len(matching_records)} existing records with matching qc_last_run values")
            
            return {
                'success': True,
                'data': matching_records,
                'matching_count': len(matching_records),
                'total_checked': len(qc_last_run_values)
            }
            
        except Exception as e:
            error_msg = f"Failed to check qc_last_run values: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'data': None
            }

    def save_fetched_data_to_output(self, data: Dict[str, Any], output_dir: Path, 
                                  filename_prefix: str = "FETCHED_DATA",
                                  create_subdir: bool = True) -> Dict[str, Any]:
        """
        Save fetched data to output directory in the required format.
        
        Args:
            data: Fetched data to save
            output_dir: Output directory
            filename_prefix: Prefix for the filename
            create_subdir: If True, create REDCAP_FETCH subdirectory, else save directly
            
        Returns:
            Dict with save results
        """
        try:
            # Create timestamped subdirectory or use provided directory directly
            if create_subdir:
                timestamp = datetime.now().strftime('%d%b%Y')
                redcap_dir = output_dir / f"REDCAP_FETCH_{timestamp}"
                redcap_dir.mkdir(parents=True, exist_ok=True)
            else:
                redcap_dir = output_dir
                redcap_dir.mkdir(parents=True, exist_ok=True)
            
            # Create filename with timestamp
            time_stamp = datetime.now().strftime('%d%b%Y_%H%M%S')
            filename = f"{filename_prefix}_{time_stamp}.json"
            file_path = redcap_dir / filename
            
            # Save data in the expected format
            export_data = {
                'fetch_metadata': {
                    'fetch_timestamp': datetime.now().isoformat(),
                    'record_count': len(data.get('data', [])),
                    'fetched_by': 'REDCap_Fetcher',
                    'fetch_type': 'QC_Status_Data'
                },
                'data': data.get('data', [])
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Fetched data saved to: {file_path}")
            
            return {
                'success': True,
                'file_path': str(file_path),
                'directory': str(redcap_dir),
                'record_count': export_data['fetch_metadata']['record_count'],
                'files_created': [str(file_path)]
            }
            
        except Exception as e:
            error_msg = f"Failed to save fetched data: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    def save_backup_files_to_directory(self, data: Dict[str, Any], output_dir: Path, 
                                      upload_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Save backup files (targeted QC data only) to specified directory.
        
        Args:
            data: Fetched data to create backups from
            output_dir: Directory to save backup files
            upload_data: List of records being uploaded (to target only those PTIDs)
            
        Returns:
            Dict with save results and file paths
        """
        try:
            timestamp = datetime.now().strftime('%d%b%Y_%H%M%S')
            saved_files = []
            
            # Get PTIDs from upload data to target specific records
            target_ptids = set()
            if upload_data:
                for record in upload_data:
                    ptid = record.get('ptid')
                    if ptid:
                        target_ptids.add(ptid)
                self.logger.info(f"Targeting QC backup for {len(target_ptids)} PTIDs: {sorted(target_ptids)}")
            
            # Create targeted QC Status data backup (only QC-related fields for targeted PTIDs)
            qc_backup_file = output_dir / f"QCStatus_SubsetData_BackupFile_{timestamp}.json"
            
            # Filter data to only include QC status fields for targeted PTIDs
            targeted_data = []
            full_data = data.get('data', [])
            
            for record in full_data:
                # If we have upload data, only include records for PTIDs being uploaded
                record_ptid = record.get('ptid')
                if upload_data and target_ptids and record_ptid not in target_ptids:
                    continue
                
                # Create filtered record with only QC status fields
                filtered_record = {}
                for field in self.qc_status_fields:
                    if field in record:
                        filtered_record[field] = record[field]
                # Always include redcap_event_name for proper record identification
                if 'redcap_event_name' in record:
                    filtered_record['redcap_event_name'] = record['redcap_event_name']
                
                # Only add record if it has some QC data
                if len(filtered_record) > 1:  # More than just redcap_event_name
                    targeted_data.append(filtered_record)
            
            qc_backup_data = {
                'qc_metadata': {
                    'fetch_timestamp': datetime.now().isoformat(),
                    'record_count': len(targeted_data),
                    'fields_included': self.qc_status_fields,
                    'target_ptids': sorted(target_ptids) if target_ptids else [],
                    'fetch_type': 'qc_status_form_targeted',
                    'purpose': 'Current QC STATUS data that will be overwritten (targeted PTIDs and fields only)'
                },
                'data': targeted_data
            }
            
            with open(qc_backup_file, 'w', encoding='utf-8') as f:
                json.dump(qc_backup_data, f, indent=2, ensure_ascii=False)
            saved_files.append(str(qc_backup_file))
            self.logger.info(f"QC STATUS targeted backup saved to: {qc_backup_file}")
            if target_ptids:
                self.logger.info(f"Targeted backup contains {len(targeted_data)} records for {len(target_ptids)} PTIDs")
            else:
                self.logger.info(f"Targeted backup contains {len(targeted_data)} records with QC data")
            
            return {
                'success': True,
                'files_created': saved_files,
                'qc_backup_file': str(qc_backup_file)
            }
            
        except Exception as e:
            error_msg = f"Failed to save backup files: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    def get_record_by_id(self, record_id: str) -> Dict[str, Any]:
        """
        Fetch a specific record by ID.
        
        Args:
            record_id: The record ID to fetch
            
        Returns:
            Dict containing the record data
        """
        return self.fetch_qc_status_data(records=[record_id])
    
    def get_project_info(self) -> Dict[str, Any]:
        """
        Get project information from REDCap.
        
        Returns:
            Dict containing project metadata
        """
        try:
            data = {
                'token': self.config.api_token,
                'content': 'project',
                'format': 'json',
                'returnFormat': 'json'
            }
            
            response = self.session.post(
                self.config.api_url,
                data=data,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            project_info = response.json()
            
            return {
                'success': True,
                'project_info': project_info
            }
            
        except Exception as e:
            error_msg = f"Failed to get project info: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    def save_fetch_results(self, fetch_results: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
        """
        Save results from fetch_for_upload to organized output structure.
        
        Args:
            fetch_results: Results from fetch_for_upload
            output_dir: Directory to save the fetched data
            
        Returns:
            Dict with save results and file paths
        """
        try:
            if not fetch_results['success']:
                return fetch_results
            
            # Create timestamped subdirectory
            timestamp = datetime.now().strftime('%d%b%Y_%H%M%S')
            fetch_dir = output_dir / f"REDCAP_FETCH_{timestamp}"
            fetch_dir.mkdir(parents=True, exist_ok=True)
            
            saved_files = {}
            
            # Save analysis results
            analysis_file = fetch_dir / f"UPLOAD_ANALYSIS_{timestamp}.json"
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(fetch_results['analysis'], f, indent=2, ensure_ascii=False)
            saved_files['analysis'] = str(analysis_file)
            self.logger.info(f"Analysis saved to: {analysis_file}")
            
            # Save complete backup data
            if fetch_results['complete_backup']['success']:
                backup_file = fetch_dir / f"COMPLETE_BACKUP_{timestamp}.json"
                backup_data = {
                    'backup_metadata': {
                        'fetch_timestamp': fetch_results['complete_backup']['fetch_timestamp'],
                        'record_count': fetch_results['complete_backup']['record_count'],
                        'fetch_type': 'complete_project_backup',
                        'purpose': 'Full backup for safety before upload'
                    },
                    'data': fetch_results['complete_backup']['data']
                }
                
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)
                saved_files['complete_backup'] = str(backup_file)
                self.logger.info(f"Complete backup saved to: {backup_file}")
            
            # Save targeted QC STATUS data
            if fetch_results['qc_status_data']['success']:
                qc_file = fetch_dir / f"QC_STATUS_TARGETED_{timestamp}.json"
                qc_data = {
                    'qc_metadata': {
                        'fetch_timestamp': fetch_results['qc_status_data']['fetch_timestamp'],
                        'record_count': fetch_results['qc_status_data']['record_count'],
                        'fields_fetched': fetch_results['qc_status_data']['fields_fetched'],
                        'target_records': fetch_results['qc_status_data']['target_records'],
                        'fetch_type': 'qc_status_form_targeted',
                        'purpose': 'Current QC STATUS data that will be overwritten'
                    },
                    'data': fetch_results['qc_status_data']['data']
                }
                
                with open(qc_file, 'w', encoding='utf-8') as f:
                    json.dump(qc_data, f, indent=2, ensure_ascii=False)
                saved_files['qc_status_data'] = str(qc_file)
                self.logger.info(f"QC STATUS data saved to: {qc_file}")
            
            # Save summary report
            summary_file = fetch_dir / f"FETCH_SUMMARY_{timestamp}.json"
            summary_data = {
                'fetch_summary': fetch_results['fetch_summary'],
                'files_created': saved_files,
                'fetch_directory': str(fetch_dir),
                'operation_timestamp': datetime.now().isoformat()
            }
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            saved_files['summary'] = str(summary_file)
            
            self.logger.info("Fetch results saved successfully!")
            self.logger.info(f"Output directory: {fetch_dir}")
            self.logger.info(f"Files created: {len(saved_files)}")
            
            return {
                'success': True,
                'output_directory': str(fetch_dir),
                'files_saved': saved_files,
                'summary': fetch_results['fetch_summary']
            }
            
        except Exception as e:
            error_msg = f"Error saving fetch results: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }