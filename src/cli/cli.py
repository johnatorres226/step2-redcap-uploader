"""Command Line Interface for UDSv4 REDCap QC Uploader."""

import json
import os
import re
import sys
from datetime import datetime
from datetime import datetime as dt
from pathlib import Path
from typing import Optional

import click

from src.config.redcap_config import REDCapConfig
from src.config.settings import Settings
from src.logging.logging_config import get_logger, setup_logging
from src.uploader.uploader import QCDataUploader

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

_TELEMETRY_DIR = Path(os.getenv("TELEMETRY_PATH") or str(project_root / "telemetry")).resolve()
_TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)

# Version from pyproject.toml
__version__ = "0.2.0"

# Initialize logger
logger = get_logger("cli")


def find_latest_qc_status_file(upload_path: Path) -> Optional[Path]:
    """
    Find the most recently created QC Status Report file.
    Expected pattern: QC_Status_Report_{DDMMMYYYY}_{HHMMSS}.json
    Falls back to QC_Status_Report_{DDMMMYYYY}.json if no timestamp format found.

    Returns the file with the latest timestamp based on filename, not file system dates.
    """
    pattern_with_time = re.compile(r"^QC_Status_Report_(\d{2}[A-Z]{3}\d{4})_(\d{6})\.json$", re.IGNORECASE)
    pattern_date_only = re.compile(r"^QC_Status_Report_(\d{2}[A-Z]{3}\d{4})\.json$", re.IGNORECASE)

    qc_files = []

    for file in upload_path.glob("QC_Status_Report_*.json"):
        match_with_time = pattern_with_time.match(file.name)
        match_date_only = pattern_date_only.match(file.name)

        if match_with_time:
            date_str, time_str = match_with_time.groups()
            try:
                file_datetime = dt.strptime(f"{date_str}_{time_str}", "%d%b%Y_%H%M%S")
                qc_files.append((file_datetime, file))
            except ValueError:
                qc_files.append((dt.fromtimestamp(file.stat().st_mtime), file))
        elif match_date_only:
            date_str = match_date_only.group(1)
            try:
                file_datetime = dt.strptime(date_str, "%d%b%Y")
                qc_files.append((file_datetime, file))
            except ValueError:
                qc_files.append((dt.fromtimestamp(file.stat().st_mtime), file))

    if not qc_files:
        return None

    qc_files.sort(key=lambda x: x[0], reverse=True)
    return qc_files[0][1]


def create_output_directory(output_dir: Optional[Path] = None, test_run: bool = False) -> Path:
    """Create output directory for the upload process."""
    if output_dir:
        output_dir = Path(output_dir)
    else:
        date_part = datetime.now().strftime("%d%b%Y")
        time_part = datetime.now().strftime("%H%M%S")
        prefix = "TEST_" if test_run else ""
        dir_name = f"{prefix}REDCAP_Uploader_{date_part}_{time_part}"
        output_dir = Path("./output") / dir_name

    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@click.group(name="udsv4-ru", invoke_without_command=True)
@click.version_option(version=__version__, prog_name="udsv4-ru")
@click.option("-i", "--initials", type=str, help="User initials for logging purposes")
@click.option(
    "-u",
    "--upload-dir",
    type=click.Path(exists=True, path_type=Path),
    help="Directory containing QC Status Report JSON files to upload",
)
@click.option("-o", "--output-dir", type=click.Path(path_type=Path), help="Directory to save upload results and logs")
@click.option("--force", is_flag=True, default=False, help="Force upload even if data appears to be already uploaded")
@click.option(
    "--test",
    "test_run",
    is_flag=True,
    default=False,
    help="Test mode: labels output directory as TEST_* without changing behavior",
)
@click.pass_context
def cli(
    ctx, initials: Optional[str], upload_dir: Optional[Path], output_dir: Optional[Path], force: bool, test_run: bool
):
    """UDSv4 REDCap Uploader - Upload QC Status Report data to REDCap.

    This tool finds the latest QC Status Report file in the upload directory
    and uploads the data to REDCap with an audit trail.

    Examples:
        udsv4-ru --initials JT
        udsv4-ru --initials JT --upload-dir ./my_data --output-dir ./my_output --force

    Commands:
      config    Show current configuration settings
    """
    if ctx.invoked_subcommand is not None:
        return

    if initials is None:
        click.echo(ctx.get_help())
        ctx.exit(0)

    setup_logging(log_level="INFO", console_output=True)

    logger.info(f"Starting UDSv4 REDCap upload process (User: {initials})")

    started_at = datetime.now()

    try:
        config = REDCapConfig.from_env()
        settings = Settings.from_env()

        uploader = QCDataUploader(config, settings)

        if not upload_dir:
            upload_dir = Path(settings.UPLOAD_READY_PATH)

        output_directory = create_output_directory(output_dir, test_run)

        logger.info(f"Upload directory: {upload_dir}")
        logger.info(f"Output directory: {output_directory}")
        logger.info(f"Force upload: {force}")

        # Step 1: Find and validate upload file
        if not upload_dir.exists():
            logger.error(f"Upload directory does not exist: {upload_dir}")
            raise click.ClickException(f"Upload directory not found: {upload_dir}")

        latest_file = find_latest_qc_status_file(upload_dir)
        if not latest_file:
            logger.error("No QC Status Report files found with expected pattern")
            json_files = list(upload_dir.glob("*.json"))
            if json_files:
                logger.info("Available JSON files:")
                for file in json_files:
                    logger.info(f"  - {file.name}")
            raise click.ClickException("No valid QC Status Report files found")

        logger.info(f"Found latest QC Status Report file: {latest_file.name}")

        # Step 2: Perform upload
        logger.info("Uploading data to REDCap...")

        upload_results_dir = output_directory / "Upload"

        upload_result = uploader.upload_qc_status_data(
            specific_file=latest_file,
            initials=initials or "",
            dry_run=False,
            force_upload=force,
            custom_output_dir=upload_results_dir,
        )

        if upload_result["success"]:
            logger.info("Upload completed successfully!")
            logger.info(f"Records processed: {upload_result.get('records_processed', 0)}")

            completed_at = datetime.now()
            telemetry = {
                "run_id": completed_at.strftime("%H%M%S"),
                "step": "redcap-uploader",
                "event_type": "RU",
                "user": initials,
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat(),
                "duration_s": round((completed_at - started_at).total_seconds(), 1),
                "status": "success",
                "payload": {
                    "source_file": latest_file.name,
                    "records_uploaded": upload_result.get("records_processed", 0),
                    "destination": "REDCap",
                    "force_upload": force,
                },
                "error": None,
            }
            telemetry_path = _TELEMETRY_DIR / f"RU_TELEMETRY_LOG_{completed_at.strftime('%H%M%S')}.json"
            with open(telemetry_path, "w", encoding="utf-8") as f:
                json.dump(telemetry, f, indent=2, ensure_ascii=False)

            logger.info(f"Telemetry log saved to: {telemetry_path}")
            logger.info(f"All outputs in: {output_directory}")
            logger.info("UDSv4 REDCap upload process completed successfully!")
        else:
            logger.error(f"Upload failed: {upload_result.get('error', 'Unknown error')}")
            raise click.ClickException("Upload process failed")

    except Exception as e:
        logger.error(f"Upload process failed: {str(e)}")
        raise click.ClickException(str(e))


@cli.command()
def config():
    """Show current configuration settings.

    Displays essential configuration and connection status.
    """
    try:
        settings = Settings.from_env()
        redcap_config = REDCapConfig.from_env()

        click.echo("=== UDSv4 REDCap Uploader Configuration ===")
        click.echo(f"Version: {__version__}")
        click.echo(f"REDCap URL: {redcap_config.api_url}")
        click.echo(f"API Token: {'✓ Set' if redcap_config.api_token else '✗ Not Set'}")
        click.echo(f"Upload Path: {settings.UPLOAD_READY_PATH}")
        click.echo(f"Output Path: {settings.OUTPUT_DIR}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


if __name__ == "__main__":
    cli()
