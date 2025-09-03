# UDSv4 REDCap QC Uploader

A comprehensive tool for uploading QC Status and Query Resolution data to REDCap with full change tracking, validation, and audit logging.

## Table of Contents

- [Quick Start](#-quick-start)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Output Structure](#output-structure)
- [Discriminatory Variable Logic](#discriminatory-variable-logic)
- [Change Tracking](#change-tracking)
- [Environment Variables](#environment-variables-env)
- [Testing](#testing)
- [Configuration](#configuration)
- [Audit Trail](#audit-trail)
- [Safety Features](#safety-features)
- [Error Handling](#error-handling)
- [Logging](#logging)
- [Support](#support)


## 🚀 Quick Start

1. **Activate the virtual environment:**

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

2. **Install the package in editable mode:**

   ```powershell
   pip install -e .
   ```

3. **Configure your environment file:**

   ```powershell
   cp .env.example .env
   # Edit .env with your REDCap credentials
   ```

4. **Run the complete upload process:**

   ```powershell
   # Complete end-to-end process (RECOMMENDED)
   udsv4-ru run --initials JT
   
   # Specify custom upload directory
   udsv4-ru run --initials JT --upload-dir ./data/json_files
   
   # Force upload even if data appears already uploaded
   udsv4-ru run --initials JT --force
   
   # Get help
   udsv4-ru --help
   ```

## Features

- **Complete End-to-End Process**: Fetches current REDCap data for backup, uploads new QC Status data, and saves comprehensive results
- **Automatic File Detection**: Finds the latest QC Status Report file based on filename timestamps
- **Data Backup**: Creates both complete and targeted backups before any uploads
- **Change Tracking**: Complete audit trail of all changes with comprehensive logging
- **Duplicate Detection**: Intelligent detection using `qc_last_run` discriminatory variable
- **Force Upload Option**: Ability to bypass duplicate detection when needed
- **Comprehensive Logging**: Detailed logging with timestamped output directories
- **CLI Interface**: Simple, streamlined command line interface

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd udsv4-redcap-qc-uploader
   ```

2. Install the package and dependencies:

   ```bash
   pip install -e .
   ```

3. Create environment file:

   ```bash
   cp .env.example .env
   ```

4. Configure your `.env` file with REDCap credentials:

   ```env
   REDCAP_API_URL=https://your-redcap-instance.com/api/
   REDCAP_API_TOKEN=your_api_token_here
   REDCAP_PROJECT_ID=your_project_id
   UPLOAD_READY_PATH=./data/upload_ready
   BACKUP_LOG_PATH=./backups
   ```

## Usage

### Command Line Interface

The tool provides a simplified CLI with the `udsv4-ru` command that performs a complete end-to-end process:

```bash
# Basic usage - processes latest QC Status Report from default directory
udsv4-ru run --initials JT

# Specify custom upload directory
udsv4-ru run --initials JT --upload-dir ./data/json_files

# Specify custom output directory
udsv4-ru run --initials JT --output-dir ./exports

# Force upload even if data appears already uploaded
udsv4-ru run --initials JT --force

# Combine options
udsv4-ru run --initials JT --upload-dir ./data --output-dir ./exports --force
```

### The Complete Process

The `run` command performs these steps automatically:

1. **Data Fetching**: Retrieves current QC Status data from REDCap for backup
2. **File Detection**: Finds the latest QC Status Report file in the upload directory
3. **Backup Creation**: Creates both complete and targeted backups of existing data
4. **Data Upload**: Uploads the new QC Status data to REDCap
5. **Result Documentation**: Saves comprehensive logs and summary files

### Command Options

- `--initials` (required): User initials for logging and audit purposes
- `--upload-dir`: Directory containing QC Status Report JSON files (defaults to UPLOAD_READY_PATH)
- `--output-dir`: Custom directory for saving results (auto-generated if not specified)
- `--force`: Force upload even if data appears to be already uploaded

### QC Status Report File Detection

The system automatically finds the most recent QC Status Report file using these patterns:

- `QC_Status_Report_DDMMMYYYY_HHMMSS.json` (preferred format with timestamp)
- `QC_Status_Report_DDMMMYYYY.json` (fallback format with date only)

Files are sorted by the timestamp in the filename to determine the latest version.


## Output Structure

Each upload process creates timestamped output directories with comprehensive results:

```text
output/
└── REDCAP_CompleteUpload_DDMMMYYYY_HHMMSS/
    ├── UPLOAD_SUMMARY.json                    # Complete process summary
    ├── REDCAP_DataFetcher_DDMMMYYYY/
    │   ├── REDCAP_PriorToUpload_BackupFile_DDMMMYYYY_HHMMSS.json
    │   └── REDCAP_QCStatus_TargetedBackup_DDMMMYYYY_HHMMSS.json
    └── REDCAP_Uploader_NewQCResults_DDMMMYYYY/
        ├── DataUploaded_DDMMMYYYY_HHMMSS.json
        ├── DataUploaded_Receipt_DDMMMYYYY_HHMMSS.json
        └── LOG_FILE.txt
```

### File Naming Conventions

- **BU Suffix**: Files ending with `_BU` contain data from **Before Upload** (backup purposes)
- **Timestamps**: Use format `DDMMMYYYY_HHMMSS` (e.g., `21Jul2025_141502`)
- **Targeted Files**: Contain only QC-related fields instead of complete records
- **Receipt Files**: Document exactly what was uploaded to REDCap
- **Summary Files**: Provide complete overview of the entire process

## Key Features

### Discriminatory Variable Logic

The system uses the `qc_last_run` field to determine if data has already been uploaded:

- Compares `qc_last_run` values between new and existing data
- Only uploads records where `qc_last_run` has changed
- Prevents duplicate uploads automatically
- Can be bypassed with `--force` flag

### Change Tracking

- **Complete Backup**: Full backup of original REDCap data before any changes
- **Targeted Backup**: Backup of only records that will be affected by the upload
- **Upload Receipts**: Detailed record of exactly what was uploaded
- **Process Summary**: Complete overview of the entire upload process saved as JSON
- **Comprehensive Logging**: Detailed logs saved to both output directory and backup location

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDCAP_API_URL` | REDCap API endpoint | Required |
| `REDCAP_API_TOKEN` | REDCap API token | Required |
| `UPLOAD_READY_PATH` | Path to JSON files for upload | `./data` |
| `BACKUP_LOG_PATH` | Path for backup logs | `./backups` |

## Testing

Run tests with:

```bash
pytest tests/
```

## Configuration

### Environment Variables (.env)

```env
REDCAP_API_URL=https://your-redcap-instance.com/api/
REDCAP_API_TOKEN=your_api_token
LOG_LEVEL=INFO
```

### Settings (config/settings.py)

- File monitoring settings
- Data validation rules
- Upload batch sizes
- Retry configurations

## Audit Trail

All changes are logged in the `logs/` directory with the following structure:

- `audit_YYYYMMDD_HHMMSS.json`: Detailed change log
- `summary_YYYYMMDD_HHMMSS.txt`: Human-readable summary
- `backup_YYYYMMDD_HHMMSS.json`: Original REDCap data backup

## Safety Features

- **File Hash Verification**: Prevents processing unchanged files
- **Data Backup**: Automatic backup of existing REDCap data
- **Dry Run Mode**: Preview changes before actual upload
- **Rollback Capability**: Detailed logs enable future rollbacks
- **Validation Checks**: Data integrity validation before upload

## Error Handling

The system includes comprehensive error handling for:

- REDCap API failures
- File access issues
- Data validation errors
- Network connectivity problems

## Logging

All operations are logged with different levels:

- `INFO`: General operation status
- `WARNING`: Non-critical issues
- `ERROR`: Critical errors requiring attention
- `DEBUG`: Detailed debugging information

## Support

For questions or issues, please contact the ADRC Data Management team.
