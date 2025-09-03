# UDSv4 REDCap QC Uploader

A comprehensive tool for uploading QC Status and Query Resolution data to REDCap with full change tracking, validation, and audit logging.

## 🚀 Quick Start

**New to this tool?** Check out the [QUICK_START.md](QUICK_START.md) guide for complete usage examples and workflow instructions.

**Basic Usage:**
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run commands (initials always required)
udsv4-redcap-uploader --initials JT [command] [options]
```

## Features

- **QC Status Upload**: Upload QC Status Report Data from JSON files
- **Query Resolution Upload**: Upload Query Resolution Data from CSV/Excel files  
- **Change Tracking**: Complete audit trail of all changes with fallback capabilities
- **Duplicate Detection**: Intelligent detection using `qc_last_run` discriminatory variable
- **End-to-End Process**: Complete fetch and upload workflow in one command
- **Comprehensive Logging**: Detailed logging with backup mechanisms
- **CLI Interface**: Easy-to-use command line interface

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
```
REDCAP_API_URL=https://your-redcap-instance.com/api/
REDCAP_API_TOKEN=your_api_token_here
REDCAP_PROJECT_ID=your_project_id
UPLOAD_READY_PATH=./data/upload_ready
BACKUP_LOG_PATH=./backups
```

## Usage

### Command Line Interface

The tool provides a CLI with the `udsv4-redcap-uploader` command:

```bash
# Upload QC Status data (initials always required)
udsv4-redcap-uploader --initials JT upload-qc-status --upload-path ./data/json_files

# Upload Query Resolution data
udsv4-redcap-uploader --initials JT upload-query-resolution --data-file ./data/queries.csv

# Export current REDCap data
udsv4-redcap-uploader --initials JT export-current-data --output-dir ./exports

# End-to-End Process (RECOMMENDED)
udsv4-redcap-uploader --initials JT end2end --dry-run

# Dry run (validation only)
udsv4-redcap-uploader --initials JT upload-qc-status --upload-path ./data --dry-run

# Force upload (skip duplicate checking)
udsv4-redcap-uploader --initials JT upload-qc-status --upload-path ./data --force
```

### Available Commands

1. **upload-qc-status**: Upload QC Status Report Data from JSON files
   - `--upload-path`: Directory containing JSON files (optional, uses UPLOAD_READY_PATH)
   - `--dry-run`: Perform validation without actual upload
   - `--force`: Force upload even if data appears already uploaded

2. **upload-query-resolution**: Upload Query Resolution Data from CSV/Excel
   - `--data-file`: Path to CSV or Excel file (required)
   - `--dry-run`: Perform validation without actual upload

3. **export-current-data**: Export current QC Status data from REDCap
   - `--output-dir`: Directory to save exported data (optional)

4. **end2end**: Complete fetch and upload process in one command
   - `--upload-path`: Directory containing JSON files (optional, uses UPLOAD_READY_PATH)
   - `--dry-run`: Perform validation without actual upload
   - `--force`: Force upload even if data appears already uploaded


## Output Structure

Each process creates timestamped output directories with specific naming conventions:


### File Naming Conventions
- **BU Suffix**: Files ending with `_BU` contain data from **Before Upload** (backup purposes)
- **Timestamps**: Use format `DDMMMYYYY_HHMMSS` (e.g., `21Jul2025_141502`)
- **Targeted Files**: Contain only QC-related fields instead of complete records

## Key Features

### Discriminatory Variable Logic

The system uses the `qc_last_run` field to determine if data has already been uploaded:
- Compares `qc_last_run` values between new and existing data
- Only uploads records where `qc_last_run` has changed
- Prevents duplicate uploads automatically
- Can be bypassed with `--force` flag

### Change Tracking

- **Fallback Files**: Complete backup of original data before any changes
- **Upload Receipts**: Detailed record of what was uploaded
- **Comprehensive Log**: Master tracking file with all operations
- **Backup Mechanism**: Automatic backup to `BACKUP_LOG_PATH`

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
```
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