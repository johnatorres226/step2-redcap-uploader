# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-05-15

### Added

- **Logging Module** (`src/logging/`): New dedicated logging infrastructure with colored terminal output using UNM brand ANSI palette (Turquoise/INFO, Cherry/ERROR, etc.), icon-prefixed log levels, and auto-detection of terminal color support
- **Telemetry Output**: CLI now writes a structured `RU_TELEMETRY_LOG_<HHMMSS>.json` file to a configurable `TELEMETRY_PATH` (defaults to `./telemetry/`) after each successful run
- **`--test` Flag**: CLI accepts `--test` to label the output directory with a `TEST_` prefix without changing upload behavior, enabling safe dry-label runs
- **CI/CD Pipeline** (`.github/workflows/ci.yml`): Comprehensive pipeline covering PR-to-main changelog and version enforcement, Ruff lint and format checks, mypy type checking, and Poetry build verification with artifact upload
- **`_get_record_identity()`** method on `QCDataUploader`: builds a stable four-tuple key `(record_id, event_name, repeat_instrument, repeat_instance)` for reliable cross-event deduplication and change tracking
- **Multi-key JSON loading**: uploader now resolves records from `data`, `participant_status`, or `records` keys, or treats the root dict as a single record when none of those keys are present

### Changed

- **CLI refactor**: Removed the `run` subcommand — the default invocation is now `udsv4-ru --initials <INITIALS>` (breaking change for callers using `udsv4-ru run`)
- **`redcap_event_instance` alias**: `uploader.py` and `data_processor.py` now automatically remap incoming `redcap_event_instance` values to `redcap_repeat_instance` before upload, matching the REDCap API expectation
- **Logging imports**: All modules (`uploader`, `fetcher`, `data_processor`, `change_tracker`, `file_monitor`, `cli`) now obtain loggers via `src.logging.logging_config.get_logger()` instead of bare `logging.getLogger()`
- **`docs/cofig.md` renamed** to `docs/config.md` (typo fix); all internal references updated

### Removed

- **`.github/workflows/build.yml`**: Replaced by the new comprehensive `ci.yml` workflow

## [0.1.0] - 2025-09-11

### Added

- **Initial Release**: Complete REDCap QC Status data uploader tool for UDSv4 events
- **CLI Interface**: Command-line interface (`udsv4-ru`) with Poetry entry point
- **End-to-End Upload Process**: Automated workflow for fetching, validating, and uploading QC data
- **Intelligent File Detection**: Automatic detection of latest QC Status Report JSON files
- **Data Backup System**:
  - Complete REDCap database backup before uploads
  - Targeted backup of records that will be modified
  - Comprehensive backup and recovery capabilities
- **Change Tracking**:
  - Full audit trail of all data changes
  - Field-level change detection and logging
  - Upload history tracking with comprehensive logs
- **Duplicate Detection**: Smart filtering using `qc_last_run` discriminatory variable
- **Force Upload Option**: Ability to bypass duplicate detection when needed
- **REDCap Integration**:
  - Quality Control Check Form instrument for REDCap projects
  - API-based data fetching and uploading
  - Structured error handling and response processing
- **Comprehensive Logging**:
  - Timestamped output directories for each run
  - Detailed logs saved to both output directory and centralized location
  - Upload receipts and data validation reports
- **Configuration Management**:
  - Environment-based configuration with `.env` support
  - Flexible settings for upload paths, backup locations, and API endpoints
- **Data Processing**:
  - JSON file validation and standardization
  - REDCap format conversion and audit trail injection
  - Robust error handling and validation checks
- **File Monitoring**:
  - File change detection using hashes and timestamps
  - Processing history tracking to prevent duplicate processing
- **Safety Features**:
  - Dry run mode for testing uploads
  - File hash verification to prevent processing unchanged files
  - Validation checks before data upload
  - Detailed rollback information in logs

### Technical Features

- **Python 3.11+** support with modern async capabilities
- **Poetry** for dependency management and CLI entry points
- **Structured Logging** with JSON output and multiple handlers
- **REDCap API** integration with timeout handling and retry logic
- **Data Validation** using Cerberus and JSON Schema
- **Testing Suite** with pytest and comprehensive test coverage
- **Code Quality** tools: Ruff for linting, MyPy for type checking

### Documentation

- Comprehensive README with installation and usage instructions
- Technical documentation for uploader internals
- Configuration guide for environment setup
- Project guidelines for development and operational guidance

