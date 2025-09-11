# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

