# UDSv4 REDCap QC Uploader

A comprehensive tool for uploading QC Status and Query Resolution data to REDCap with full change tracking, validation, and audit logging.

## Table of Contents

- [Features](#features)
- [Installation](#installation-poetry-first)
- [Usage](#usage)
- [Output Structure](#output-structure)
- [Discriminatory Variable Logic](#discriminatory-variable-logic)
- [Change Tracking](#change-tracking)
- [Testing](#testing)
- [Configuration](#configuration)
- [Audit Trail](#audit-trail)
- [Safety Features](#safety-features)

## Features

- **Complete End-to-End Process**: Fetches current REDCap data for backup, uploads new QC Status data, and saves comprehensive results
- **Automatic File Detection**: Finds the latest QC Status Report file based on filename timestamps
- **Data Backup**: Creates both complete and targeted backups before any uploads
- **Change Tracking**: Complete audit trail of all changes with comprehensive logging
- **Duplicate Detection**: Intelligent detection using `qc_last_run` discriminatory variable
- **Force Upload Option**: Ability to bypass duplicate detection when needed
- **Comprehensive Logging**: Detailed logging with timestamped output directories
- **CLI Interface**: Simple, streamlined command line interface

## REDCap Instrument Requirements

This system requires specific REDCap instruments and configurations for UDSv4 events. The `redcap-tools/` directory contains essential tools that must be imported into your REDCap project:

- **Quality Control Check Form** (`QualityControlCheck_2025-09-10_1403.zip`): Required instrument for QC validation workflow

Please ensure this instrument is added to every UDSv4 event in your REDCap project before using the uploader.

## Installation (Poetry-first)

This project now uses Poetry to manage dependencies and provide the CLI entry point. The steps below assume a modern Python 3.11+ environment.

1. Install Poetry

2. Ensure `poetry` is on your PATH

On Windows, Poetry's shim is typically at `%AppData%\Python\Scripts\poetry.exe`. If `poetry --version` fails, add that folder to your user PATH (or follow the Poetry installer instructions).

3. Clone and install

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

- macOS / Linux:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

4. Clone and install

```powershell
# clone the repository
git clone https://github.com/johnatorres226/step2-redcap-uploader.git
cd step2-redcap-uploader

# install project dependencies (creates a virtual environment automatically)
poetry install
```

5. Environment

- Create a `.env` file in the project root. See `.env.example` for required variables (REDCAP_API_URL, REDCAP_API_TOKEN, LOG_LEVEL, etc.).
- Create local directories used by the app (if they don't already exist):

```powershell
mkdir output
mkdir logs
```

6. Verify the installation

```powershell
poetry --version
poetry run udsv4-ru --version
poetry run udsv4-ru --help
```

Notes

- If you need to uninstall or reinstall Poetry, use the official installer/uninstaller documented at [python-poetry.org](https://python-poetry.org).
- The project supports running under Poetry-created virtual environments. Use `poetry run` to invoke the CLI or `poetry shell` to activate the environment.

## Usage

The preferred way to run the CLI is via Poetry. The package exposes the `udsv4-ru` command when installed with Poetry.

Basic examples:

```powershell
# Process the latest QC Status Report from the default upload directory
poetry run udsv4-ru --initials TEXT

# Specify a custom upload directory
poetry run udsv4-ru --initials TEXT --upload-dir ./data/json_files

# Specify a custom output directory
poetry run udsv4-ru --initials TEXT --output-dir ./exports

# Force upload even if data appears already uploaded
poetry run udsv4-ru --initials TEXT --force

# Combine options
poetry run udsv4-ru --initials TEXT --upload-dir ./data --output-dir ./exports --force
```

Command options

- `--initials` (required): User initials for logging and audit purposes
- `--upload-dir`: Directory containing QC Status Report JSON files (defaults to UPLOAD_READY_PATH)
- `--output-dir`: Custom directory for saving results (auto-generated if not specified)
- `--force`: Force upload even if data appears to be already uploaded

The remaining sections of the README (Features, Output Structure, Change Tracking, Environment Variables, Testing, etc.) remain unchanged and document the behavior of the tool.

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

## Testing

Run tests with:

```bash
pytest tests/
```

## Configuration Details

### Settings (config/settings.py)

- File monitoring settings
- Data validation rules
- Upload batch sizes
- Retry configurations

## Audit Trail

All changes are logged in the `logs/` directory with the following structure.

## Safety Features

- **File Hash Verification**: Prevents processing unchanged files
- **Data Backup**: Automatic backup of existing REDCap data
- **Dry Run Mode**: Preview changes before actual upload
- **Rollback Capability**: Detailed logs enable future rollbacks
- **Validation Checks**: Data integrity validation before upload
