# UDSv4 REDCap QC Uploader - Quick Start Guide

## Overview

The UDSv4 REDCap QC Uploader is a command-line tool designed to manage QC Status and Query Resolution data between your local files and REDCap. It provides a complete workflow for exporting current data, uploading new data, and tracking all changes with comprehensive logging and fallback capabilities.

## Installation

1. **Activate the virtual environment:**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

2. **Install the package in editable mode:**
   ```powershell
   pip install -e .
   ```

3. **Verify installation:**
   ```powershell
   udsv4-redcap-uploader --help
   ```

## CLI Command Structure

All commands follow this pattern:
```
udsv4-redcap-uploader --initials [YOUR_INITIALS] [COMMAND] [OPTIONS]
```

**Required Parameter:**
- `--initials`: Your initials (used for logging and audit trails)

## Available Commands

### 1. Upload QC Status Data
Upload QC Status Report data from JSON files to REDCap.

```powershell
udsv4-redcap-uploader --initials JT upload-qc-status [OPTIONS]
```

**Options:**
- `--upload-path PATH`: Directory containing JSON files (default: from UPLOAD_READY_PATH in .env)
- `--dry-run`: Preview changes without uploading
- `--force`: Force upload even if data appears already uploaded

**Example:**
```powershell
udsv4-redcap-uploader --initials JT upload-qc-status --upload-path "C:\data\json_files" --dry-run
```

### 2. Upload Query Resolution Data
Upload Query Resolution data from CSV/Excel files to REDCap.

```powershell
udsv4-redcap-uploader --initials JT upload-query-resolution [OPTIONS]
```

**Options:**
- `--data-file PATH`: Path to CSV/Excel file with query resolution data (required)
- `--dry-run`: Preview changes without uploading

**Example:**
```powershell
udsv4-redcap-uploader --initials JT upload-query-resolution --data-file "C:\data\queries.csv" --dry-run
```

### 3. Export Current Data
Export current QC Status data from REDCap for backup or analysis.

```powershell
udsv4-redcap-uploader --initials JT export-current-data [OPTIONS]
```

**Options:**
- `--output-dir PATH`: Directory to save exported data (default: ./output)

**Example:**
```powershell
udsv4-redcap-uploader --initials JT export-current-data --output-dir "C:\backups"
```

### 4. Monitor Files
Monitor a directory for new files and display processing status.

```powershell
udsv4-redcap-uploader --initials JT monitor-files [OPTIONS]
```

**Options:**
- `--upload-path PATH`: Directory to monitor (default: from UPLOAD_READY_PATH in .env)

**Example:**
```powershell
udsv4-redcap-uploader --initials JT monitor-files --upload-path "C:\data\incoming"
```

### 5. End-to-End Process (NEW!)
Complete fetch and upload in one command.

```powershell
udsv4-redcap-uploader --initials JT end2end [OPTIONS]
```

**Options:**
- `--upload-path PATH`: Directory containing JSON files (default: from UPLOAD_READY_PATH in .env)
- `--dry-run`: Fetch current data and preview upload without actually uploading
- `--force`: Force upload even if data appears already uploaded

**Example (Dry Run):**
```powershell
udsv4-redcap-uploader --initials JT end2end --dry-run
```

**Example (Actual Upload):**
```powershell
udsv4-redcap-uploader --initials JT end2end --upload-path "C:\data\json_files"
```

## Complete Workflow Example

### Option 1: Simple End-to-End Process (RECOMMENDED)

**Step 1: Test with dry-run**
```powershell
udsv4-redcap-uploader --initials JT end2end --dry-run
```

**Step 2: Execute actual upload**
```powershell
udsv4-redcap-uploader --initials JT end2end
```

### Option 2: Manual Step-by-Step Process

Here's how to run a complete fetcher/uploader process manually:

### Step 1: Export Current Data (Backup)
First, create a backup of current REDCap data:
```powershell
udsv4-redcap-uploader --initials JT export-current-data --output-dir ".\backups"
```

### Step 2: Test Upload (Dry Run)
Preview what will be uploaded without making changes:
```powershell
udsv4-redcap-uploader --initials JT upload-qc-status --dry-run
```

### Step 3: Upload QC Status Data
Upload the actual QC Status data:
```powershell
udsv4-redcap-uploader --initials JT upload-qc-status
```

### Step 4: Upload Query Resolution Data (if needed)
If you have query resolution data to upload:
```powershell
udsv4-redcap-uploader --initials JT upload-query-resolution --data-file ".\data\query_resolutions.csv"
```

## Output Structure

Each upload creates a timestamped subdirectory in the format: `REDCAP_UPLOAD_DDMMMYYYY`

**Generated Files:**
- `FALLBACK_FILE_DDMMMYYYY.json`: Backup data for reverting changes
- `DATA_UPLOAD_RECEIPT_DDMMMYYYY.json`: Receipt of uploaded data
- `LOG_FILE.txt`: Detailed log of the upload process

**Example Output Directory:**
```
output/
└── REDCAP_UPLOAD_21JUL2025/
    ├── FALLBACK_FILE_21JUL2025.json
    ├── DATA_UPLOAD_RECEIPT_21JUL2025.json
    └── LOG_FILE.txt
```

## Configuration

The tool uses environment variables from `.env`:

```properties
# REDCap Configuration
REDCAP_API_TOKEN=your_token_here
REDCAP_API_URL=https://your-redcap-instance/api/
ADRC_REDCAP_PROJECT_ID=15746

# Data Paths
UPLOAD_READY_PATH=C:\path\to\json\files
BACKUP_LOG_PATH=C:\path\to\backup\logs

# Application Settings
LOG_LEVEL=INFO
DRY_RUN_DEFAULT=false
```

## Smart Upload Logic

The tool includes intelligent duplicate detection:

- **QC Last Run Check**: Compares `qc_last_run` values to prevent duplicate uploads
- **Change Tracking**: Only uploads records that have actually changed
- **Audit Trail**: Maintains comprehensive logs of all operations

## Safety Features

1. **Dry Run Mode**: Test uploads without making changes
2. **Fallback Files**: Automatic backup creation before uploads
3. **Comprehensive Logging**: Track every operation with timestamps
4. **Duplicate Prevention**: Smart logic prevents accidental re-uploads
5. **Force Override**: Option to bypass duplicate detection when needed

## Troubleshooting

### Common Issues

1. **"ModuleNotFoundError"**: Ensure virtual environment is activated
2. **"Permission denied"**: Check file permissions and paths
3. **"API connection failed"**: Verify REDCap credentials in `.env`
4. **"No files found"**: Check UPLOAD_READY_PATH configuration

### Getting Help

```powershell
# General help
udsv4-redcap-uploader --help

# Command-specific help
udsv4-redcap-uploader --initials JT upload-qc-status --help
```

## Best Practices

1. **Always use dry-run first**: Test uploads before executing
2. **Regular backups**: Export current data before major uploads
3. **Monitor logs**: Check LOG_FILE.txt for detailed operation records
4. **Use meaningful initials**: Helps with audit trails and troubleshooting
5. **Validate data**: Ensure JSON/CSV files are properly formatted before upload

## One-Command Complete Process

For a fully automated process, you can chain commands:

```powershell
# Complete workflow in sequence
udsv4-redcap-uploader --initials JT export-current-data && `
udsv4-redcap-uploader --initials JT upload-qc-status --dry-run && `
udsv4-redcap-uploader --initials JT upload-qc-status
```

This will:
1. Export current data as backup
2. Preview the upload (dry-run)
3. Execute the actual upload

## Support

For technical support or questions:
- Check the `logs/` directory for detailed error messages
- Review the generated `LOG_FILE.txt` for operation details
- Ensure all environment variables are properly configured in `.env`
