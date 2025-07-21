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
    """Upload QC Status Report Data from JSON files."""
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
@click.option('--output-dir', type=click.Path(path_type=Path),
              help='Directory to save exported data')
@click.pass_context
def export_current_data(ctx, output_dir: Optional[Path]):
    """Export current QC Status data from REDCap."""
    initials = ctx.obj['initials']
    logger = ctx.obj['logger']
    
    logger.info(f"Starting data export process (User: {initials})")
    
    try:
        # Initialize components
        config = REDCapConfig.from_env()
        
        # Import the fetcher here to avoid circular imports
        from src.uploader.fetcher import REDCapFetcher
        
        # Initialize fetcher
        fetcher = REDCapFetcher(config, logger)
        
        # Set default output directory
        if not output_dir:
            output_dir = Path('./output')
        
        logger.info(f"Output directory: {output_dir}")
        
        # Fetch current data from REDCap
        logger.info("Fetching current QC Status data from REDCap...")
        fetch_result = fetcher.fetch_qc_status_data()
        
        if not fetch_result['success']:
            logger.error(f"Failed to fetch data: {fetch_result['error']}")
            raise click.ClickException("Failed to fetch data from REDCap")
        
        logger.info(f"Successfully fetched {fetch_result['record_count']} records")
        
        # Save to output directory
        save_result = fetcher.save_fetched_data_to_output(
            fetch_result, 
            output_dir, 
            "EXPORTED_QC_DATA"
        )
        
        if save_result['success']:
            logger.info(f"Data exported successfully!")
            logger.info(f"Export file: {save_result['file_path']}")
            logger.info(f"Records exported: {save_result['record_count']}")
        else:
            logger.error(f"Failed to save exported data: {save_result['error']}")
            raise click.ClickException("Failed to save exported data")
            
    except Exception as e:
        logger.error(f"Export process failed: {str(e)}")
        raise click.ClickException(str(e))


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
        
        # Step 2: Save fetched data to output directory
        output_dir = Path('./output')
        output_dir.mkdir(exist_ok=True)
        
        save_result = fetcher.save_fetched_data_to_output(
            current_data_result, 
            output_dir, 
            "CURRENT_REDCAP_DATA"
        )
        
        if save_result['success']:
            logger.info(f"Current REDCap data saved to: {save_result['file_path']}")
        
        # Step 3: Check for files to upload
        if upload_path.exists():
            json_files = list(upload_path.glob("*.json"))
            logger.info(f"Found {len(json_files)} JSON files to process")
            
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
                else:
                    logger.info("Step 4: Performing actual upload...")
                    upload_result = uploader.upload_qc_status_data(
                        upload_path=upload_path,
                        initials=initials,
                        dry_run=False,
                        force_upload=force
                    )
                    
                    if upload_result['success']:
                        logger.info(f"Upload completed successfully!")
                        logger.info(f"Records processed: {upload_result.get('records_processed', 0)}")
                        logger.info(f"Output directory: {upload_result.get('output_directory', 'N/A')}")
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


@cli.command()
@click.option('--upload-path', type=click.Path(exists=True, path_type=Path),
              help='Path to monitor for new files')
@click.pass_context
def monitor_files(ctx, upload_path: Optional[Path]):
    """Monitor directory for new files and display processing status."""
    initials = ctx.obj['initials']
    logger = ctx.obj['logger']
    
    logger.info(f"Starting file monitoring (User: {initials})")
    
    try:
        # Determine upload path
        settings = Settings.from_env()
        if not upload_path:
            upload_path = Path(settings.UPLOAD_READY_PATH)
        
        logger.info(f"Monitoring path: {upload_path}")
        
        if upload_path.exists():
            files = list(upload_path.rglob("*"))
            data_files = [f for f in files if f.is_file() and f.suffix in ['.json', '.csv', '.xlsx']]
            
            logger.info(f"Found {len(data_files)} data files:")
            for file in data_files:
                stats = file.stat()
                last_modified = datetime.fromtimestamp(stats.st_mtime)
                logger.info(f"  - {file.name} (Size: {stats.st_size} bytes, Modified: {last_modified.isoformat()})")
        else:
            logger.warning(f"Path does not exist: {upload_path}")
            
    except Exception as e:
        logger.error(f"Failed to monitor files: {str(e)}")
        raise click.ClickException(str(e))


if __name__ == '__main__':
    cli()