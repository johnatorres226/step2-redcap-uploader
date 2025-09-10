# UDSv4 REDCap QC Uploader

A comprehensive tool for uploading QC Status and Query Resolution data to REDCap with full change tracking, validation, and audit logging.

## Table of Contents

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

### Step 1: Install Poetry  

**Windows (PowerShell)** — run the official installer script:

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

---

### Step 2: Where Poetry is Installed  

- Core installation (virtual environment):  
  `%AppData%\pypoetry\venv`

- Shim executable (used on PATH):  
  `%AppData%\Python\Scripts\poetry.exe`

The shim is what allows you to type `poetry` anywhere in the terminal.

---

### Step 3: Verify Installation  

```powershell
poetry --version
where.exe poetry
```

Or browse to the folder:

```powershell
cd $env:APPDATA\Python\Scripts
dir poetry.exe
```

---

### Step 4: Add Poetry to PATH (if not already available)

**Option A — PowerShell**

```powershell
$poetryPath = Join-Path $env:APPDATA 'Python\Scripts'
[Environment]::SetEnvironmentVariable(
  'Path',
  [Environment]::GetEnvironmentVariable('Path','User') + ';' + $poetryPath,
  'User'
)
```

- Close and reopen your terminal (or VS Code).  
- Restart your computer if necessary.

**Option B — Manual (Windows UI)**

1. Press **Start** → type *Environment Variables* → open **Edit the system environment variables**  
2. Click **Environment Variables…**  
3. Under **User variables**, select `Path` → **Edit…**  
4. Click **New**, then paste:  

   ```
   %AppData%\Python\Scripts
   ```

5. OK → OK to save  
6. Close and reopen your terminal (or VS Code)
7. May require a system restart if not udpated immediately

---

### Step 5: Reinstall or Uninstall if Needed  

To uninstall Poetry:

```powershell
python -m poetry self uninstall
```

*(or manually delete `%AppData%\pypoetry` and `%AppData%\Python\Scripts\poetry.exe` if broken)*

Reinstall with the installer script again if necessary.

---

### Linux / macOS  

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### Step 2: Clone and Setup Project

```bash
# Clone the repository
git clone https://github.com/johnatorres226/step1-nacc-validator.git
cd step1-nacc-validator

# Install dependencies (creates virtual environment automatically)
poetry install

# Verify installation
poetry run udsv4-qc --help
```

### Step 3: Environment Configuration

Create a `.env` file in the project root, and refer to `.env.example` for required variables.

### Step 4: Create Output and Log Directory

```bash
mkdir output
mkdir logs
```

### Step 5: Verify Setup

```bash
# Check configuration
poetry run udsv4-ru config

# Test CLI functionality
poetry run udsv4-ru --version


## Usage

### Command Line Interface

The tool provides a simplified CLI with the `udsv4-ru` command that performs a complete end-to-end process:

```bash
# Basic usage - processes latest QC Status Report from default directory
poetry run udsv4-ru  --initials TEXT

# Specify custom upload directory
poetry run udsv4-ru --initials TEXT --upload-dir ./data/json_files

# Specify custom output directory
poetry run udsv4-ru --initials TEXT --output-dir ./exports

# Force upload even if data appears already uploaded
poetry run udsv4-ru --initials TEXT --force

# Combine options
poetry run udsv4-ru --initials TEXT --upload-dir ./data --output-dir ./exports --force
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

| Variable              | Description                   | Default       |
|-----------------------|-------------------------------|---------------|
| `REDCAP_API_URL`      | REDCap API endpoint           | Required      |
| `REDCAP_API_TOKEN`    | REDCap API token              | Required      |
| `UPLOAD_READY_PATH`   | Path to JSON files for upload | `./data`      |
| `BACKUP_LOG_PATH`     | Path for backup logs          | `./backups`   |

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
