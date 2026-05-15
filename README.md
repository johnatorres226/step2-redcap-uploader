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
# Upload the latest QC Status Report from the default upload directory
poetry run udsv4-ru --initials JT

# Specify a custom upload directory
poetry run udsv4-ru --initials JT --upload-dir ./data/json_files

# Specify a custom output directory
poetry run udsv4-ru --initials JT --output-dir ./exports

# Force upload even if data appears already uploaded
poetry run udsv4-ru --initials JT --force

# Combine options
poetry run udsv4-ru --initials JT --upload-dir ./data --output-dir ./exports --force

# View current configuration
poetry run udsv4-ru config
```

### Command Options

The default behavior is to upload QC Status Report data to REDCap.

Options:

- `-i, --initials` (required): User initials for logging and audit purposes
- `-u, --upload-dir`: Directory containing QC Status Report JSON files (defaults to `UPLOAD_READY_PATH`)
- `-o, --output-dir`: Custom directory for saving results (auto-generated if not specified)
- `--force`: Force upload even if data appears to be already uploaded
- `--test`: Label the output directory with a `TEST_` prefix without changing upload behavior

### Subcommands

**`config`** - Show current configuration settings

Displays essential configuration and connection status without requiring any options.

## Output Structure

Each run creates a timestamped directory under `output/` and a telemetry log under `telemetry/`:

```text
output/
└── REDCAP_Uploader_DDMMMYYYY_HHMMSS/        # e.g. REDCAP_Uploader_15May2026_142305
    └── Upload/
        ├── DataUploaded_DDMMMYYYY_HHMMSS.json          # Records sent to REDCap (with audit fields)
        └── DataUploaded_Recipt_DDMMMYYYY_HHMMSS.json   # Upload receipt with API response metadata

telemetry/                                    # Configurable via TELEMETRY_PATH env var
└── RU_TELEMETRY_LOG_HHMMSS.json             # Structured run telemetry (timing, status, record count)

logs/
└── comprehensive_upload_log.json             # Appended after every successful upload

backups/
└── comprehensive_upload_log_backup_*.json    # Rotating backup of the upload log
```

With `--test`, the output directory is prefixed `TEST_REDCAP_Uploader_DDMMMYYYY_HHMMSS/`.

### File Naming Conventions

- **Timestamps**: Use format `DDMMMYYYY_HHMMSS` (e.g., `15May2026_142305`)
- **`DataUploaded_*`**: The exact records imported to REDCap, including injected audit trail fields
- **`DataUploaded_Recipt_*`**: Upload receipt — records the API response, record count, source file, and user initials (note: `Recipt` spelling is preserved from the original implementation)
- **`RU_TELEMETRY_LOG_*`**: Structured JSON with run metadata: start/end time, duration, status, source file, and record count

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

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `REDCAP_API_URL` | ✓ | — | REDCap instance API endpoint |
| `REDCAP_API_TOKEN` | ✓ | — | Project-specific API token |
| `REDCAP_PROJECT_ID` | | — | Optional project ID |
| `REDCAP_TIMEOUT` | | `30` | API request timeout (seconds) |
| `REDCAP_MAX_RETRIES` | | `3` | API retry attempts |
| `REDCAP_RETRY_DELAY` | | `1.0` | Delay between retries (seconds) |
| `UPLOAD_READY_PATH` | | `./data` | Directory scanned for QC Status JSON files |
| `BACKUP_LOG_PATH` | | `./backups` | Directory for upload log backups |
| `LOG_LEVEL` | | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `LOG_PATH` | | `./logs` | Directory for persistent log files |
| `OUTPUT_DIR` | | `./output` | Root directory for per-run output |
| `DATA_DIR` | | `./data` | Project data directory |
| `TELEMETRY_PATH` | | `./telemetry` | Directory for telemetry JSON logs |
| `BATCH_SIZE` | | `100` | Upload batch size |
| `VALIDATE_DATA` | | `true` | Enable pre-upload data validation |
| `CHECK_FILE_CHANGES` | | `true` | Use file hash/timestamp change detection |

### Settings (`src/config/settings.py`)

Full runtime configuration with environment-driven overrides. Use `Settings.from_env()` to load. See [docs/config.md](docs/config.md) for details.

## Audit Trail

All changes are recorded in `logs/`:

- `comprehensive_upload_log.json` — appended after every upload; contains source file, record count, user, timestamp, and upload type
- `backups/comprehensive_upload_log_backup_*.json` — rotating backup of the upload history
- `audit_*.json` / `summary_*.txt` — per-operation field-level change sets written by `ChangeTracker`

See [docs/uploader.md](docs/uploader.md) for the full schema of change tracking artifacts.

## Safety Features

- **File Hash Verification**: Prevents processing unchanged files
- **Data Backup**: Automatic backup of existing REDCap data
- **Dry Run Mode**: Preview changes before actual upload
- **Rollback Capability**: Detailed logs enable future rollbacks
- **Validation Checks**: Data integrity validation before upload
