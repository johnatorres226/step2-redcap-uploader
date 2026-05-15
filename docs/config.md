# Configuration (src/config)

This document explains the configuration elements used by the project. Files in `src/config`:

- `settings.py` — application-level settings and runtime defaults
- `redcap_config.py` — REDCap API configuration and payload helpers

## settings.py (Settings)

Primary responsibilities:

- Provide default runtime configuration
- Load and expose environment-driven overrides via `Settings.from_env()`
- Create necessary directories (`data/`, `logs/`, `backups/`, `output/`) on initialization

Key fields and usage:

- File monitoring
  - `CHECK_FILE_CHANGES` (bool): Whether to check file modification and size before reprocessing
  - `FILE_HASH_ALGORITHM` (str): Hash algorithm used by `FileMonitor.get_file_hash()`

- Data processing
  - `BATCH_SIZE` (int): Default batch size used by processors (100)
  - `MAX_RETRIES` (int): Number of retry attempts for transient operations
  - `RETRY_DELAY` (float): Time between retries (seconds)

- Validation
  - `VALIDATE_DATA` (bool): Toggle for running validations
  - `STRICT_VALIDATION` (bool): If enabled, stricter checks are applied in `DataProcessor`

- Logging
  - `LOG_LEVEL` (str): Default log level (reads `LOG_LEVEL` env var)
  - `LOG_FORMAT` (str): Format string for logs
  - `LOG_TO_FILE` (bool): Whether to write logs to files
  - `LOG_TO_CONSOLE` (bool): Whether to write logs to console

- Directories
  - `BASE_DIR`: Root package path resolved from source
  - `DATA_DIR`: Project `data/` dir for inputs
  - `LOGS_DIR`: `logs/` directory for persistent logs
  - `BACKUPS_DIR`: `BACKUP_LOG_PATH` default backup location
  - `OUTPUT_DIR`: `output/` directory where per-run artifacts are saved

- Upload paths and tracking
  - `UPLOAD_READY_PATH` (str): Where the uploader watches for JSON files (default `./data`)
  - `BACKUP_LOG_PATH` (str): Where to put backup logs (default `./backups`)
  - `LAST_PROCESSED_FILE` (str) and `FILE_TRACKING_DB` (str): File tracking names

- Safety features
  - `DRY_RUN_DEFAULT` (bool)
  - `BACKUP_BEFORE_UPLOAD` (bool)
  - `CONFIRM_UPLOADS` (bool)

Using `from_env()`:

- Call `Settings.from_env()` to respect environment variable overrides.

Examples:

- `BATCH_SIZE` via env: `BATCH_SIZE=200`
- `UPLOAD_READY_PATH` via env: `UPLOAD_READY_PATH=./data/upload_ready`

## redcap_config.py (REDCapConfig)


- Encapsulate API connection details for REDCap


- `api_token` (str): Project-specific REDCap API token (required)


- `max_retries` (int) and `retry_delay` (float): Retry defaults for API operations


- `REDCapConfig.from_env(project_id=None)` reads `REDCAP_API_URL` and `REDCAP_API_TOKEN` from environment.


Payload helpers:

- `get_export_payload(**kwargs)` - returns a dict with standard export parameters (token, content, format, etc.)
- `get_import_payload(data: str, **kwargs)` - returns a dict with standard import parameters for record import

Compatibility helpers:

- Module-level fallbacks: when env vars are present at import time, the module exposes `adrc_api_key`, `adrc_redcap_url`, and default `uds_events`. If env is missing, these are set to `None`/`[]` to avoid import errors.

## Best practices and operational notes

- Always set `REDCAP_API_URL` and `REDCAP_API_TOKEN` in your `.env` or environment before running the CLI.
- Configure `UPLOAD_READY_PATH` if you need a different folder for incoming JSON files.
- Use `BACKUP_BEFORE_UPLOAD=true` to guarantee a full backup run before attempting any imports.
- For debugging API issues, increase `LOG_LEVEL` to `DEBUG` and inspect `LOG_FILE.txt` and `logs/` output.


For the upload process details and file-level behaviors, see `docs/uploader.md`.
