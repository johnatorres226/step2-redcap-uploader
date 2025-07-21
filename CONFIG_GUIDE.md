# Configuration Guide

## Environment Variables (.env file)

Copy this template to your `.env` file and replace the placeholder values:

```bash
# REDCap API Configuration
REDCAP_API_URL=https://your-redcap-instance.com/api/
REDCAP_API_TOKEN=your_api_token_here
REDCAP_PROJECT_ID=your_project_id

# Application Settings
LOG_LEVEL=INFO
CHECK_FILE_CHANGES=true
BATCH_SIZE=100
MAX_RETRIES=3
VALIDATE_DATA=true
DRY_RUN_DEFAULT=false

# REDCap Connection Settings
REDCAP_TIMEOUT=30
REDCAP_MAX_RETRIES=3
REDCAP_RETRY_DELAY=1.0
```

## How to Get Your REDCap API Token

1. Log into your REDCap project
2. Go to "API" in the left sidebar
3. Click "Request API Token" 
4. Once approved, copy the token to your .env file

## Required Data Format

Your Excel/CSV file should include:
- `ptid`: Patient/participant ID (required)
- `redcap_event_name`: REDCap event name (if using longitudinal project)
- Other data fields matching your REDCap project

### Example CSV Format:
```csv
ptid,redcap_event_name,field1,field2,field3
001,baseline_arm_1,value1,value2,value3
002,baseline_arm_1,value1,value2,value3
```

## Running the Uploader

### 1. Setup (first time only)
```bash
# Install dependencies
pip install -r requirements.txt

# Or install in development mode with all features
pip install -e .[all]
```

### 2. Preview Changes (Dry Run)
```bash
python main.py --input data/your_file.xlsx --project-id 12345 --dry-run
```

### 3. Upload Data
```bash
python main.py --input data/your_file.xlsx --project-id 12345
```

### 4. Upload Specific Events/Forms
```bash
python main.py --input data/your_file.xlsx --project-id 12345 \
  --events "baseline_arm_1,followup_1_arm_1" \
  --forms "demographics,medical_history"
```

## Command Line Options

- `--input, -i`: Input file path (required)
- `--project-id, -p`: REDCap project ID
- `--events, -e`: Comma-separated list of events
- `--forms, -f`: Comma-separated list of forms
- `--dry-run, -d`: Preview changes without uploading
- `--force-upload`: Upload even if file hasn't changed
- `--skip-validation`: Skip data validation
- `--batch-size`: Records per batch (default: 100)
- `--verbose, -v`: Enable debug logging
- `--quiet, -q`: Only show errors

## Safety Features

### File Change Detection
The system tracks file hashes to avoid processing the same file twice. Use `--force-upload` to override.

### Audit Logging
All changes are logged in the `logs/` directory:
- `audit_YYYYMMDD_HHMMSS.json`: Detailed change log
- `summary_YYYYMMDD_HHMMSS.txt`: Human-readable summary

### Data Backup
Original REDCap data is backed up to `backups/` before any changes.

### Dry Run Mode
Always test with `--dry-run` first to preview changes.

## Troubleshooting

### Common Issues

1. **"Import error"**: Run `pip install -r requirements.txt`
2. **"Missing required columns"**: Check your data format
3. **"API token invalid"**: Verify your .env configuration
4. **"No changes detected"**: File may not have changed (use `--force-upload`)

### Getting Help
```bash
python main.py --help
```

### Log Files
Check `uploader.log` and files in `logs/` directory for detailed information.

## File Structure After Setup

```
├── main.py                    # Main script
├── setup.py                   # Setup script
├── requirements.txt           # Dependencies
├── .env                       # Your configuration
├── uploader.log              # Application logs
├── config/                    # Configuration modules
├── src/                       # Source code
├── data/                      # Input data files
│   └── example_data.csv
├── logs/                      # Audit logs
├── backups/                   # Data backups
└── fetcher.py                # Legacy compatibility
```
