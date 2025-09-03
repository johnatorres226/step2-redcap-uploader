# Uploader Internals (src/uploader)

This document describes the core uploader modules, functions, outputs, process flow, logging behavior, monitoring, and completion criteria. It covers:

- `uploader.QCDataUploader`
- `fetcher.REDCapFetcher`
- `data_processor.DataProcessor`
- `change_tracker.ChangeTracker`
- `file_monitor.FileMonitor`

## High-level process flow

1. CLI triggers `QCDataUploader.upload_qc_status_data()` via `udsv4-ru run`.
2. Uploader locates the latest JSON files in the upload directory.
3. Fetcher obtains current REDCap data (complete backup and targeted QC fields).
4. DataProcessor validates and standardizes data, converting to REDCap format.
5. Uploader adds audit trail entries and prepares backup/fallback structures.
6. Uploader performs the REDCap import API call and handles responses.
7. Results, receipts, backups, and comprehensive logs are written to disk.

## `QCDataUploader` (src/uploader/uploader.py)

Responsibilities:

- Orchestrates the end-to-end upload process for QC Status and Query Resolution data.
- Creates per-run output directories and log files.
- Coordinates with `REDCapFetcher`, `DataProcessor`, `FileMonitor`, and `ChangeTracker`.

Key methods and behavior:

- `upload_qc_status_data(upload_path, initials, dry_run=False, force_upload=False, custom_output_dir=None)`
  - Reads JSON files (via `_find_latest_files`), validates structure (`_load_json_file`, `_validate_qc_data`).
  - Filters new records using `_filter_new_records()` which compares `qc_last_run` values to current REDCap data.
  - Adds audit trail entries using `DataProcessor.add_audit_trail()`.
  - Creates backup data with `_create_backup_data()` and persists receipts and uploaded data files.
  - Uses `_upload_to_redcap()` to POST to REDCap API; handles JSON or plain-text responses and error modes (timeouts, request errors).
  - Tracking: `_track_upload()` writes to a comprehensive upload log and backups it to `BACKUPS_DIR`.

- `upload_query_resolution_data(data_file, initials, dry_run=False)`
  - Loads CSV/Excel (`_load_csv_file`, `_load_excel_file`), converts to REDCap format (`_convert_to_redcap_format`), creates fallback backup, and uploads similarly to QC status flow.

- Internal helpers:
  - `_create_output_directory(upload_type)` — creates structured output directories and initial `LOG_FILE.txt`.
  - `_find_latest_files(directory, pattern)` — lists files sorted by modification time; used to detect candidate JSON files.
  - `_validate_qc_data(data)` — validates required fields (`ptid`, `qc_last_run`) and reports validation errors.
  - `_filter_new_records(new_data, current_data)` — implements `qc_last_run` discriminatory logic (only upload when changed).
  - `_upload_to_redcap(data)` — prepares request payload and handles API response parsing and error mapping.

Outputs and files created:

- `DataUploaded_*.json` — saved copy of the uploaded data including audit fields
- `DataUploaded_Recipt_*.json` — upload receipt containing API response and metadata (note: `Recipt` spelling preserved)
- `LOG_FILE.txt` — run level log file in output directory
- `UPLOAD_SUMMARY.json` — high-level summary for combined runs (might be present in CLI flow)
- `comprehensive_upload_log.json` & backup — global uploads history under `logs/` and `backups/`

Failure modes and error handling:

- Validation failures: uploader skips file and logs errors, continues processing other files
- API timeouts and failures: `_upload_to_redcap` returns structured error dicts with `error_type` for retry logic
- Unexpected exceptions: returned as `success: False` with error messages in the result dict

## `REDCapFetcher` (src/uploader/fetcher.py)

Responsibilities:

- Interacts with the REDCap API for fetching and exporting project data
- Provides analysis of upload files to inform targeted fetching
- Saves fetched results to organized output directories

Key methods:

- `analyze_upload_data(upload_path)`
  - Scans JSON upload files and summarizes fields, record IDs, and `qc_last_run` values.
  - Returns `recommended_fetch_strategy` (full backup, targeted QC field list, specific record focuses).

- `fetch_complete_backup_data()`
  - Calls REDCap export API to fetch full project data as a safety backup.

- `fetch_qc_status_form_data(record_ids=None, qc_fields=None)`
  - Fetches only the QC-related fields for all or specific records; used to create targeted backups and enable differential uploads.

- `fetch_for_upload(upload_path)`
  - High-level method combining analysis and both complete + targeted fetches; returns combined results for saving.

- `fetch_qc_status_data(records=None, specific_fields=None)`
  - General QC STATUS fetcher; returns raw REDCap records array and metadata.

- `save_fetched_data_to_output(fetch_results, output_dir)` and `save_backup_files_to_directory(data, output_dir, upload_data)`
  - Save structured JSON files with metadata and create `FETCH_SUMMARY_*`, `COMPLETE_BACKUP_*`, and `QC_STATUS_TARGETED_*` files.

Outputs and artifacts produced:

- `UPLOAD_ANALYSIS_*.json` — analysis of upload input files
- `COMPLETE_BACKUP_*.json` — full project backup for safety
- `QC_STATUS_TARGETED_*.json` — targeted QC STATUS form backup for PTIDs and fields that will be modified
- `FETCH_SUMMARY_*.json` — summary of fetch operations

Logging and error handling:

- Logs API errors and partial responses; includes response snippets on failure to aid debugging
- Returns structured `{'success': False, 'error': ...}` responses when fetches fail

## `DataProcessor` (src/uploader/data_processor.py)

Responsibilities:

- Validate data format and required columns
- Clean and standardize values (strip whitespace, handle encodings)
- Convert data to REDCap-compatible format (strings, yes/no normalization)
- Add audit trail entries to `qc_results`

Key methods:

- `load_file(file_path)` — load CSV or Excel into pandas DataFrame
- `validate_required_columns(df, required_columns)` — ensures required columns exist
- `validate_data_types(df, column_types)` — check types for specified columns
- `validate_unique_keys(df, key_columns)` — ensure unique key combinations
- `clean_data(df)` — housekeeping, remove empty rows, standardize names
- `standardize_redcap_fields(df)` — ensure REDCap system fields exist
- `add_audit_trail(upload_data, current_redcap_data, user_initials)` — append formatted audit entries to `qc_results`

Validation outputs:

- `get_validation_summary()` returns errors, warnings, and `is_valid` flag

## `ChangeTracker` (src/uploader/change_tracker.py)

Responsibilities:

- Compute per-field differences between current and new data
- Record `FieldChange` entries and persist change sets
- Maintain upload history and enable change reporting

Key artifacts:

- `change_tracking.json` — a list of `ChangeSet` objects that contain `FieldChange` details
- `upload_tracking.json` — summary entries for each upload operation

Key methods:

- `track_upload(upload_type, file_paths, initials, records_count)` — appends upload metadata to upload_tracking
- `track_changes(operation_id, file_path, file_hash, old_data, new_data)` — compares and persists `ChangeSet`
- `generate_change_report(operation_id)` — returns an aggregated report (changes by form/field, totals)

Comparison logic:

- Compares non-`redcap_` fields across old and new records
- Builds keys using `record_id|event|repeat_instrument|repeat_instance` to compare matching rows
- Creates `FieldChange` with metadata for each changed field

## `FileMonitor` (src/uploader/file_monitor.py)

Responsibilities:

- Monitor the upload-ready directory for new or changed files
- Maintain `file_tracking.json` with `FileInfo` entries including file hash, size, modified time, records count

Key methods:

- `has_file_changed(file_path)` — quick comparison using modification time and size; fallback to true on error
- `get_file_hash(file_path, algorithm='sha256')` — compute file hash when needed
- `mark_file_processed(file_path, records_count)` — record processed file info and write history
- `get_new_files()` — return list of new/changed files for processing
- `get_file_status()` — return status list for UI/monitoring

Monitoring notes:

- `has_file_changed` uses timestamp and size checks for performance; if more rigorous checks are required, enable hashing checks.
- `cleanup_old_entries(days=30)` helps prune history records for files that have been removed or inactive.

## End-to-end completion criteria

A run is considered successful when:

- The uploader received a `success: True` result and created upload receipts and uploaded-data files.
- `UPLOAD_SUMMARY.json` (CLI flow) or per-run `LOG_FILE.txt` indicates completion and output directory path.
- `comprehensive_upload_log.json` contains an appended entry for the upload.
- Backup artifacts (complete or targeted) were written to the output directory or backup path.

For failed runs:

- Check the run-level `LOG_FILE.txt`, `comprehensive_upload_log.json`, and any `DataUploaded_Recipt_*` or `FETCH_SUMMARY_*` files.
- Use `change_tracking.json` to inspect partial changes and plan rollback if necessary.

## Operational tips

- For debugging API errors, set `LOG_LEVEL=DEBUG` and inspect the `LOG_FILE.txt` in the run output directory.
- Automate regular `COMPLETE_BACKUP_*` exports (via scheduled runs) to maintain recovery points.


---

If you want, I can also extract sample JSON structures for receipts, fetch results, and change sets to include as appendices in this doc.
