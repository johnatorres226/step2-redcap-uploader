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

from config.redcap_config import REDCapConfig
from config.settings import Settings


def create_end2end_output_directory() -> Path:
    """Create a single consolidated output directory for end2end process."""
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


@click.group()
@click.option('--initials', required=True, type=str, 
              help='User initials for logging purposes')
@click.pass_context
def cli(ctx, initials: str):
    """UDSv4 REDCap QC Uploader - A tool for managing QC Status and Query Resolution data."""
    ctx.ensure_object(dict)
    ctx.obj['initials'] = initials
    ctx.obj['logger'] = setup_logging(initials)


@cli.command()
@click.option('--upload-path', type=click.Path(exists=True, path_type=Path),
              help='Path to directory containing JSON files to upload')
@click.option('--dry-run', is_flag=True, default=False,
              help='Perform a dry run without actually uploading data')
@click.option('--force', is_flag=True, default=False,
              help='Force upload even if data appears to be already uploaded')
@click.pass_context
def upload_qc_status(ctx, upload_path: Optional[Path], dry_run: bool, force: bool):
    """
    Upload QC Status Report Data from JSON files.
    
    This command uploads QC status data to REDCap and automatically maintains 
    an audit trail in the 'qc_results' field. Each upload adds an entry with:
    [Date Stamp] {qc_status value} {qc_run_by}; 
    
    This creates a complete history of all QC runs for each record.
    """
    initials = ctx.obj['initials']
    logger = ctx.obj['logger']
    
    logger.info(f"Starting QC Status upload process (User: {initials})")
    
    try:
        # Initialize components
        config = REDCapConfig.from_env()
        settings = Settings.from_env()
        
        # Determine upload path
        if not upload_path:
            upload_path = Path(settings.UPLOAD_READY_PATH)
        
        logger.info(f"Upload path: {upload_path}")
        logger.info(f"Dry run: {dry_run}")
        logger.info(f"Force upload: {force}")
        
        # For now, just show what we found
        if upload_path.exists():
            json_files = list(upload_path.glob("*.json"))
            logger.info(f"Found {len(json_files)} JSON files")
            for file in json_files:
                logger.info(f"  - {file.name}")
        else:
            logger.warning(f"Upload path does not exist: {upload_path}")
            
    except Exception as e:
        logger.error(f"Failed to process upload: {str(e)}")
        raise click.ClickException(str(e))


@cli.command()
@click.option('--data-file', type=click.Path(exists=True, path_type=Path),
              required=True, help='Path to CSV/Excel file with query resolution data')
@click.option('--dry-run', is_flag=True, default=False,
              help='Perform a dry run without actually uploading data')
@click.pass_context
def upload_query_resolution(ctx, data_file: Path, dry_run: bool):
    """Upload Query Resolution Data from CSV/Excel file."""
    initials = ctx.obj['initials']
    logger = ctx.obj['logger']
    
    logger.info(f"Starting Query Resolution upload process (User: {initials})")
    logger.info(f"Data file: {data_file}")
    logger.info(f"Dry run: {dry_run}")
    
    # Basic implementation for now
    logger.info("Query resolution upload functionality - coming soon!")


@cli.command()
@click.option('--upload-path', type=click.Path(exists=True, path_type=Path),
              help='Path to directory containing JSON files to upload')
@click.option('--dry-run', is_flag=True, default=False,
              help='Perform fetch and preview upload without actually uploading data')
@click.option('--force', is_flag=True, default=False,
              help='Force upload even if data appears to be already uploaded')
@click.pass_context
def end2end(ctx, upload_path: Optional[Path], dry_run: bool, force: bool):
    """Complete end-to-end process: fetch current data and upload new data."""
    initials = ctx.obj['initials']
    logger = ctx.obj['logger']
    
    logger.info(f"Starting end-to-end process (User: {initials})")
    
    try:
        # Create consolidated end2end output directory
        end2end_output_dir = create_end2end_output_directory()
        logger.info(f"End2End output directory: {end2end_output_dir}")
        
        # Initialize components
        config = REDCapConfig.from_env()
        settings = Settings.from_env()
        
        # Import the uploader here to avoid circular imports
        from src.uploader.uploader import QCDataUploader
        from src.uploader.fetcher import REDCapFetcher
        
        # Initialize uploader and fetcher
        uploader = QCDataUploader(config, settings, logger)
        fetcher = REDCapFetcher(config, logger)
        
        # Determine upload path
        if not upload_path:
            upload_path = Path(settings.UPLOAD_READY_PATH)
        
        logger.info(f"Upload path: {upload_path}")
        logger.info(f"Dry run: {dry_run}")
        logger.info(f"Force upload: {force}")
        
        # Step 1: Fetch current data from REDCap
        logger.info("Step 1: Fetching current data from REDCap...")
        current_data_result = fetcher.fetch_qc_status_data()
        
        if not current_data_result['success']:
            logger.error(f"Failed to fetch current data: {current_data_result['error']}")
            raise click.ClickException("Failed to fetch current REDCap data")
        
        logger.info(f"Successfully fetched {current_data_result['record_count']} records from REDCap")
        
        # Step 2: Save fetched data to consolidated end2end directory
        # Create fetch subdirectory
        fetch_dir = end2end_output_dir / f"REDCAP_DataFetcher_{datetime.now().strftime('%d%b%Y')}"
        
        save_result = fetcher.save_fetched_data_to_output(
            current_data_result, 
            fetch_dir, 
            "REDCAP_PriorToUpload_BackupFile",
            create_subdir=False
        )
        
        if save_result['success']:
            logger.info(f"Current REDCap data saved to: {save_result['file_path']}")
        else:
            backup_result = {'success': False, 'files_created': []}
        
        # Step 3: Check for files to upload and determine what records will be uploaded
        upload_data_preview = []
        if upload_path.exists():
            json_files = list(upload_path.glob("*.json"))
            logger.info(f"Found {len(json_files)} JSON files to process")
            
            if json_files:
                # Preview what will be uploaded to create targeted backup
                for json_file in json_files:
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            file_data = json.load(f)
                        
                        if isinstance(file_data, list):
                            upload_data_preview.extend(file_data)
                        elif isinstance(file_data, dict) and 'data' in file_data:
                            upload_data_preview.extend(file_data['data'])
                        else:
                            upload_data_preview.append(file_data)
                    except Exception as e:
                        logger.warning(f"Could not preview {json_file.name}: {str(e)}")
                
                # Create targeted backup based on upload data
                backup_result = fetcher.save_backup_files_to_directory(
                    current_data_result,
                    fetch_dir,
                    upload_data_preview
                )
                
                if backup_result['success']:
                    logger.info(f"Targeted backup file created: {len(backup_result['files_created'])} files")
            else:
                backup_result = {'success': False, 'files_created': []}
        else:
            backup_result = {'success': False, 'files_created': []}
            
        # Step 4: Process upload if files exist
        if upload_path.exists():
            json_files = list(upload_path.glob("*.json"))
            
            if json_files:
                # Step 4: Process upload (dry run or actual)
                if dry_run:
                    logger.info("Step 4: Performing dry run - previewing upload...")
                    logger.info("DRY RUN MODE: Would upload the following files:")
                    for file in json_files:
                        logger.info(f"  - {file.name}")
                        
                        # Load and validate file content
                        try:
                            with open(file, 'r', encoding='utf-8') as f:
                                file_data = json.load(f)
                            
                            if isinstance(file_data, list):
                                logger.info(f"    Records in file: {len(file_data)}")
                                # Check for qc_last_run values
                                qc_runs = [record.get('qc_last_run') for record in file_data if record.get('qc_last_run')]
                                if qc_runs:
                                    logger.info(f"    QC Last Run values: {set(qc_runs)}")
                            else:
                                logger.info(f"    File content type: {type(file_data)}")
                                
                        except Exception as e:
                            logger.warning(f"    Could not preview file content: {str(e)}")
                    
                    logger.info("DRY RUN COMPLETE: No data was uploaded to REDCap")
                    
                    # Create dry run log
                    dry_run_log = {
                        'end2end_timestamp': datetime.now().isoformat(),
                        'user_initials': initials,
                        'dry_run': True,
                        'force_upload': force,
                        'fetch_results': {
                            'records_fetched': current_data_result['record_count'],
                            'current_data_backup': save_result.get('file_path', 'N/A'),
                            'targeted_qc_backup': backup_result.get('qc_backup_file', 'N/A'),
                            'fetch_directory': str(fetch_dir)
                        },
                        'dry_run_results': {
                            'files_analyzed': [f.name for f in json_files],
                            'would_process': True
                        }
                    }
                    
                    # Save dry run log
                    dry_run_log_file = end2end_output_dir / "Dryrun_Summary.json"
                    with open(dry_run_log_file, 'w', encoding='utf-8') as f:
                        json.dump(dry_run_log, f, indent=2, ensure_ascii=False)
                    
                    logger.info(f"Dry run summary saved to: {dry_run_log_file}")
                    logger.info(f"All outputs in: {end2end_output_dir}")
                else:
                    logger.info("Step 4: Performing actual upload...")
                    
                    # Create upload subdirectory
                    upload_dir = end2end_output_dir / f"REDCAP_Uploader_NewQCResults_{datetime.now().strftime('%d%b%Y')}"
                    
                    upload_result = uploader.upload_qc_status_data(
                        upload_path=upload_path,
                        initials=initials,
                        dry_run=False,
                        force_upload=force,
                        custom_output_dir=upload_dir
                    )
                    
                    if upload_result['success']:
                        logger.info(f"Upload completed successfully!")
                        logger.info(f"Records processed: {upload_result.get('records_processed', 0)}")
                        
                        # Create comprehensive end2end log
                        end2end_log = {
                            'end2end_timestamp': datetime.now().isoformat(),
                            'user_initials': initials,
                            'dry_run': dry_run,
                            'force_upload': force,
                            'fetch_results': {
                                'records_fetched': current_data_result['record_count'],
                                'current_data_backup': save_result.get('file_path', 'N/A'),
                                'targeted_qc_backup': backup_result.get('qc_backup_file', 'N/A'),
                                'fetch_directory': str(fetch_dir)
                            },
                            'upload_results': {
                                'records_processed': upload_result.get('records_processed', 0),
                                'files_uploaded': [f.name for f in json_files],
                                'receipt_file': upload_result.get('receipt_file', 'N/A'),
                                'uploaded_data_file': upload_result.get('uploaded_data_file', 'N/A'),
                                'upload_directory': str(upload_dir),
                                'fallback_files': [backup_result.get('qc_backup_file', 'N/A')]
                            },
                            'comprehensive_log_updated': True
                        }
                        
                        # Save end2end log
                        end2end_log_file = end2end_output_dir / "END2END_SUMMARY.json"
                        with open(end2end_log_file, 'w', encoding='utf-8') as f:
                            json.dump(end2end_log, f, indent=2, ensure_ascii=False)
                        
                        logger.info(f"End2End summary saved to: {end2end_log_file}")
                        logger.info(f"All outputs in: {end2end_output_dir}")
                    else:
                        logger.error(f"Upload failed: {upload_result.get('error', 'Unknown error')}")
                        raise click.ClickException("Upload process failed")
            else:
                logger.warning("No JSON files found to upload")
        else:
            logger.warning(f"Upload path does not exist: {upload_path}")
        
        logger.info("End-to-end process completed successfully!")
        
    except Exception as e:
        logger.error(f"End-to-end process failed: {str(e)}")
        raise click.ClickException(str(e))


@cli.command()
@click.option('--upload-path', type=click.Path(exists=True, path_type=Path),
              help='Path to directory containing JSON files to analyze')
@click.option('--output-dir', type=click.Path(path_type=Path), default='./output',
              help='Directory to save fetched data')
@click.pass_context
def fetch(ctx, upload_path: Optional[Path], output_dir: Path):
    """Analyze upload data and perform fetching of REDCap data."""
    initials = ctx.obj['initials']
    logger = ctx.obj['logger']
    
    logger.info(f"Starting fetch process (User: {initials})")
    
    try:
        # Initialize components
        config = REDCapConfig.from_env()
        settings = Settings.from_env()
        
        from src.uploader.fetcher import REDCapFetcher
        
        # Initialize fetcher
        fetcher = REDCapFetcher(config, logger)
        
        # Determine upload path
        if not upload_path:
            upload_path = Path(settings.UPLOAD_READY_PATH)
        
        logger.info(f"Upload path: {upload_path}")
        logger.info(f"Output directory: {output_dir}")
        
        # Ensure output directory exists
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Perform fetch
        logger.info("Starting fetch process...")
        fetch_results = fetcher.fetch_for_upload(upload_path)
        
        if not fetch_results['success']:
            logger.error(f"Fetch failed: {fetch_results['error']}")
            raise click.ClickException("Fetch process failed")
        
        # Save the results
        save_results = fetcher.save_fetch_results(fetch_results, output_dir)
        
        if save_results['success']:
            logger.info("Fetch completed successfully!")
            logger.info(f"Output directory: {save_results['output_directory']}")
            
            # Display summary
            summary = save_results['summary']
            logger.info("Fetch Summary:")
            logger.info(f"  - Files analyzed: {summary['files_analyzed']}")
            logger.info(f"  - Records to update: {summary['records_to_update']}")
            logger.info(f"  - Backup records fetched: {summary['backup_records']}")
            logger.info(f"  - QC records fetched: {summary['qc_records']}")
            logger.info(f"  - QC fields: {summary['qc_fields']}")
            
            # List saved files
            logger.info("Files created:")
            for file_type, file_path in save_results['files_saved'].items():
                logger.info(f"  - {file_type}: {Path(file_path).name}")
        else:
            logger.error(f"Failed to save fetch results: {save_results['error']}")
            raise click.ClickException("Failed to save fetch results")
        
    except Exception as e:
        logger.error(f"Fetch process failed: {str(e)}")
        raise click.ClickException(str(e))


if __name__ == '__main__':
    cli()