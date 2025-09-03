"""Command Line Interface for UDSv4 REDCap QC Uploader."""

import os
import sys
import json
import click
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.redcap_config import REDCapConfig
from src.config.settings import Settings

"""
Cli Commands Overview:
- run: Complete end-to-end process to upload QC Status Report data to REDCap

"""

import re
from datetime import datetime as dt


def find_latest_qc_status_file(upload_path: Path) -> Optional[Path]:
    """
    Find the most recently created QC Status Report file.
    Expected pattern: QC_Status_Report_{DDMMMYYYY}_{HHMMSS}.json
    Falls back to QC_Status_Report_{DDMMMYYYY}.json if no timestamp format found.
    
    Returns the file with the latest timestamp based on filename, not file system dates.
    """
    pattern_with_time = re.compile(r'^QC_Status_Report_(\d{2}[A-Z]{3}\d{4})_(\d{6})\.json$', re.IGNORECASE)
    pattern_date_only = re.compile(r'^QC_Status_Report_(\d{2}[A-Z]{3}\d{4})\.json$', re.IGNORECASE)
    
    qc_files = []
    
    # Look for QC Status Report files
    for file in upload_path.glob("QC_Status_Report_*.json"):
        match_with_time = pattern_with_time.match(file.name)
        match_date_only = pattern_date_only.match(file.name)
        
        if match_with_time:
            date_str, time_str = match_with_time.groups()
            try:
                # Parse date and time from filename
                file_datetime = dt.strptime(f"{date_str}_{time_str}", "%d%b%Y_%H%M%S")
                qc_files.append((file_datetime, file))
            except ValueError:
                # If date parsing fails, fall back to file system date
                qc_files.append((dt.fromtimestamp(file.stat().st_mtime), file))
        elif match_date_only:
            date_str = match_date_only.group(1)
            try:
                # Parse date only (assume midnight)
                file_datetime = dt.strptime(date_str, "%d%b%Y")
                qc_files.append((file_datetime, file))
            except ValueError:
                # If date parsing fails, fall back to file system date
                qc_files.append((dt.fromtimestamp(file.stat().st_mtime), file))
    
    if not qc_files:
        return None
    
    # Sort by datetime and return the most recent
    qc_files.sort(key=lambda x: x[0], reverse=True)
    return qc_files[0][1]


def create_output_directory(output_dir: Optional[Path] = None) -> Path:
    """Create output directory for the upload process."""
    if output_dir:
        output_dir = Path(output_dir)
    else:
        # Generate timestamp in same format as fetcher: DDMMMYYYY_HHMMSS
        timestamp = datetime.now().strftime('%d%b%Y_%H%M%S')
        dir_name = f"REDCAP_CompleteUpload_{timestamp}"
        output_dir = Path('./output') / dir_name
    
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def setup_logging(initials: str) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger("udsv4_redcap_uploader")
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger


@click.group(name='udsv4-ru')
def cli():
    """UDSv4 REDCap Uploader - A tool for uploading QC Status data to REDCap."""
    pass


@cli.command()
@click.option('-i', '--initials', required=True, type=str,
              help='User initials for logging purposes')
@click.option('-u', '--upload-dir', type=click.Path(exists=True, path_type=Path),
              help='Directory containing QC Status Report JSON files to upload')
@click.option('-o', '--output-dir', type=click.Path(path_type=Path),
              help='Directory to save upload results and logs')
@click.option('--force', is_flag=True, default=False,
              help='Force upload even if data appears to be already uploaded')
def run(initials: str, upload_dir: Optional[Path], output_dir: Optional[Path], force: bool):
    """
    Run the complete QC Status Report upload process.
    
    This command performs a complete end-to-end process:
    1. Fetches current data from REDCap for backup
    2. Finds the latest QC Status Report file in upload directory 
    3. Uploads the data to REDCap with audit trail
    4. Saves all results and logs to output directory
    """
    logger = setup_logging(initials)
    logger.info(f"Starting UDSv4 REDCap upload process (User: {initials})")
    
    try:
        # Initialize components
        config = REDCapConfig.from_env()
        settings = Settings.from_env()
        
        # Import the uploader here to avoid circular imports
        from src.uploader.uploader import QCDataUploader
        from src.uploader.fetcher import REDCapFetcher
        
        # Initialize uploader and fetcher
        uploader = QCDataUploader(config, settings, logger)
        fetcher = REDCapFetcher(config, logger)
        
        # Determine upload directory
        if not upload_dir:
            upload_dir = Path(settings.UPLOAD_READY_PATH)
        
        # Create output directory
        output_directory = create_output_directory(output_dir)
        
        logger.info(f"Upload directory: {upload_dir}")
        logger.info(f"Output directory: {output_directory}")
        logger.info(f"Force upload: {force}")
        
        # Step 1: Fetch current data from REDCap
        logger.info("Step 1: Fetching current data from REDCap...")
        current_data_result = fetcher.fetch_qc_status_data()
        
        if not current_data_result['success']:
            logger.error(f"Failed to fetch current data: {current_data_result['error']}")
            raise click.ClickException("Failed to fetch current REDCap data")
        
        logger.info(f"Successfully fetched {current_data_result['record_count']} records from REDCap")
        
        # Step 2: Save fetched data to output directory
        # Create fetch subdirectory
        fetch_dir = output_directory / f"REDCAP_DataFetcher_{datetime.now().strftime('%d%b%Y')}"
        
        save_result = fetcher.save_fetched_data_to_output(
            current_data_result, 
            fetch_dir, 
            "REDCAP_PriorToUpload_BackupFile",
            create_subdir=False
        )
        
        if save_result['success']:
            logger.info(f"Current REDCap data saved to: {save_result['file_path']}")
        
        # Step 3: Find and validate upload file
        if not upload_dir.exists():
            logger.error(f"Upload directory does not exist: {upload_dir}")
            raise click.ClickException(f"Upload directory not found: {upload_dir}")
        
        latest_file = find_latest_qc_status_file(upload_dir)
        if not latest_file:
            logger.error("No QC Status Report files found with expected pattern")
            # Show available files for debugging
            json_files = list(upload_dir.glob("*.json"))
            if json_files:
                logger.info("Available JSON files:")
                for file in json_files:
                    logger.info(f"  - {file.name}")
            raise click.ClickException("No valid QC Status Report files found")
        
        logger.info(f"Found latest QC Status Report file: {latest_file.name}")
        
        # Step 4: Create targeted backup
        backup_result = {'success': False, 'files_created': []}
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
            
            upload_data_preview = []
            if isinstance(file_data, list):
                upload_data_preview.extend(file_data)
            elif isinstance(file_data, dict) and 'data' in file_data:
                upload_data_preview.extend(file_data['data'])
            else:
                upload_data_preview.append(file_data)
            
            # Create targeted backup based on upload data
            backup_result = fetcher.save_backup_files_to_directory(
                current_data_result,
                fetch_dir,
                upload_data_preview
            )
            
            if backup_result['success']:
                logger.info(f"Targeted backup file created: {len(backup_result['files_created'])} files")
                
        except Exception as e:
            logger.warning(f"Could not create targeted backup: {str(e)}")
        
        # Step 5: Perform upload
        logger.info("Step 5: Uploading data to REDCap...")
        
        # Create upload subdirectory
        upload_results_dir = output_directory / f"REDCAP_Uploader_NewQCResults_{datetime.now().strftime('%d%b%Y')}"
        
        upload_result = uploader.upload_qc_status_data(
            upload_path=upload_dir,
            initials=initials,
            dry_run=False,
            force_upload=force,
            custom_output_dir=upload_results_dir
        )
        
        if upload_result['success']:
            logger.info(f"Upload completed successfully!")
            logger.info(f"Records processed: {upload_result.get('records_processed', 0)}")
            
            # Create comprehensive summary log
            summary_log = {
                'upload_timestamp': datetime.now().isoformat(),
                'user_initials': initials,
                'force_upload': force,
                'upload_file': latest_file.name,
                'fetch_results': {
                    'records_fetched': current_data_result['record_count'],
                    'current_data_backup': save_result.get('file_path', 'N/A'),
                    'targeted_qc_backup': backup_result.get('qc_backup_file', 'N/A'),
                    'fetch_directory': str(fetch_dir)
                },
                'upload_results': {
                    'records_processed': upload_result.get('records_processed', 0),
                    'receipt_file': upload_result.get('receipt_file', 'N/A'),
                    'uploaded_data_file': upload_result.get('uploaded_data_file', 'N/A'),
                    'upload_directory': str(upload_results_dir)
                }
            }
            
            # Save summary log
            summary_log_file = output_directory / "UPLOAD_SUMMARY.json"
            with open(summary_log_file, 'w', encoding='utf-8') as f:
                json.dump(summary_log, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Upload summary saved to: {summary_log_file}")
            logger.info(f"All outputs in: {output_directory}")
            logger.info("UDSv4 REDCap upload process completed successfully!")
        else:
            logger.error(f"Upload failed: {upload_result.get('error', 'Unknown error')}")
            raise click.ClickException("Upload process failed")
        
    except Exception as e:
        logger.error(f"Upload process failed: {str(e)}")
        raise click.ClickException(str(e))


if __name__ == '__main__':
    cli()