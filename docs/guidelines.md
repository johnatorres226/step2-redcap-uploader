# Project Guidelines

This document provides an overview of the UDSv4 REDCap QC Uploader project, describes the end-to-end process, and references the detailed configuration and uploader documentation.

Summary:

- Purpose: Safely upload QC Status and Query Resolution data to REDCap with robust validation, change tracking, and backups.
- Main entry points: CLI (`udsv4-ru run`) and the `QCDataUploader` class in `src/uploader/uploader.py`.
- Supporting modules: `src/config/*` (configuration), `src/uploader/*` (fetcher, uploader, data processing, monitoring, change tracking).

Contents of this file:

- Process overview and flow
- Logging and monitoring guidance
- Where to find configuration and uploader details (links to other docs)

## Process overview

The uploader implements a safe, auditable, end-to-end workflow with the following high-level steps:

1. Preparation and environment
   - Ensure environment variables are set (see `docs/cofig.md` for details).
   - Place QC Status JSON files in the upload-ready directory (default: `./data` or configured `UPLOAD_READY_PATH`).

2. Run the end-to-end command
   - Use the CLI: `udsv4-ru run --initials <INITIALS>`
   - Options: `--upload-dir`, `--output-dir`, `--force` (see CLI help for details)

3. Fetch current REDCap data for backup
   - The fetcher (`REDCapFetcher`) creates a full project backup and targeted QC backups.  The backup files are stored in a timestamped output directory.

4. Analyze upload files and target fetching
   - The fetcher analyzes JSON files to determine which fields and PTIDs will be affected, then fetches targeted QC STATUS fields for those records.

5. Validate and prepare upload data
   - `DataProcessor` performs validation, standardization, and conversion to REDCap import format.
   - Duplicate detection is performed using the `qc_last_run` field; the `--force` flag bypasses this check.

6. Create backups and audit trail
   - Complete and targeted backups are saved. The uploader adds audit trail entries to `qc_results` and generates receipt and uploaded-data files.

7. Upload to REDCap
   - Data is sent via the REDCap import API. The uploader handles API responses, retries, and error modes.

8. Save summary and tracking information
   - Comprehensive `UPLOAD_SUMMARY.json`, `LOG_FILE.txt`, receipt files, uploaded-data files, and change-tracking logs are stored in the output directory and `logs/`.

## Logging and monitoring

- Output directories: Generated under `./output/REDCAP_CompleteUpload_<DDMMMYYYY_HHMMSS>/` or `./output/REDCAP_UPLOADER_<TYPE>_<DDMMMYYYY>/` depending on the flow.
- Log files created per-run: `LOG_FILE.txt`, `UPLOAD_SUMMARY.json`, `DataUploaded_*`, `DataUploaded_Recipt_*` (note spelling retained), and fetcher output files.
- Change tracking: `logs/change_tracking.json` and `logs/upload_tracking.json` record detailed per-field changes and upload history.
- Central comprehensive log: `logs/comprehensive_upload_log.json` and additional backups in `backups/`.

Operational guidance:

- Review `LOG_FILE.txt` in the run output directory for run-level messages.
- Use `logs/comprehensive_upload_log.json` to inspect historical uploads.
- `FileMonitor` (see `docs/uploader.md`) maintains `file_tracking.json` inside the upload-ready directory to detect changed/new files.

## References

- Configuration: `docs/cofig.md` (documents `src/config/settings.py` and `src/config/redcap_config.py`)
- Uploader internals: `docs/uploader.md` (describes uploader classes, fetcher, data processor, change tracker, file monitor)


---

For detailed developer guidance and examples, see the linked docs above.
