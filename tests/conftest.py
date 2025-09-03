"""Test configuration and fixtures for the UDSv4 REDCap QC Uploader test suite."""

import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, MagicMock
import pytest
import sys

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.redcap_config import REDCapConfig
from src.config.settings import Settings


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_logger():
    """Create a test logger."""
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add console handler for test output
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


@pytest.fixture
def mock_redcap_config():
    """Create a mock REDCap configuration."""
    config = Mock(spec=REDCapConfig)
    config.api_url = "https://test-redcap.example.com/api/"
    config.api_token = "test_api_token_123456789"
    config.project_id = "12345"
    config.timeout = 30
    config.verify_ssl = True
    return config


@pytest.fixture
def test_settings(temp_dir):
    """Create test settings with temporary directories."""
    settings = Mock(spec=Settings)
    settings.BASE_DIR = temp_dir
    settings.DATA_DIR = temp_dir / "data"
    settings.LOGS_DIR = temp_dir / "logs"
    settings.BACKUPS_DIR = temp_dir / "backups"
    settings.OUTPUT_DIR = temp_dir / "output"
    settings.UPLOAD_READY_PATH = str(temp_dir / "data")
    settings.BACKUP_LOG_PATH = str(temp_dir / "backups")
    settings.BATCH_SIZE = 100
    settings.MAX_RETRIES = 3
    settings.RETRY_DELAY = 0.1  # Faster for tests
    settings.VALIDATE_DATA = True
    settings.STRICT_VALIDATION = False
    settings.FILE_HASH_ALGORITHM = "sha256"
    settings.CHECK_FILE_CHANGES = True
    settings.BACKUP_BEFORE_UPLOAD = True
    settings.CONFIRM_UPLOADS = False  # Don't ask for confirmation in tests
    settings.DRY_RUN_DEFAULT = False
    
    # Create test directories
    for directory in [settings.DATA_DIR, settings.LOGS_DIR, settings.BACKUPS_DIR, settings.OUTPUT_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    
    return settings


@pytest.fixture
def sample_qc_data():
    """Create sample QC status data for testing."""
    return [
        {
            "record_id": "UDS001",
            "redcap_event_name": "baseline_arm_1",
            "ptid": "UDS001",
            "qc_status_complete": "2",
            "qc_visit_date": "2025-08-15",
            "qc_last_run": "15AUG2025",
            "qc_notes": "Initial QC check completed",
            "qc_status": "1",
            "qc_results": "All checks passed",
            "qc_run_by": "JT",
            "quality_control_check_complete": "2"
        },
        {
            "record_id": "UDS002",
            "redcap_event_name": "baseline_arm_1",
            "ptid": "UDS002",
            "qc_status_complete": "2",
            "qc_visit_date": "2025-08-16",
            "qc_last_run": "16AUG2025",
            "qc_notes": "Second QC check",
            "qc_status": "2",
            "qc_results": "Minor issues found, corrected",
            "qc_run_by": "JT",
            "quality_control_check_complete": "2"
        },
        {
            "record_id": "UDS003",
            "redcap_event_name": "followup_1_arm_1",
            "ptid": "UDS003",
            "qc_status_complete": "1",
            "qc_visit_date": "2025-08-17",
            "qc_last_run": "17AUG2025",
            "qc_notes": "Follow-up QC",
            "qc_status": "1",
            "qc_results": "",
            "qc_run_by": "JT",
            "quality_control_check_complete": "1"
        }
    ]


@pytest.fixture
def sample_qc_file(temp_dir, sample_qc_data):
    """Create a sample QC status JSON file."""
    file_path = temp_dir / "data" / "QC_Status_Report_21AUG2025_120000.json"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(sample_qc_data, f, indent=2)
    
    return file_path


@pytest.fixture
def old_qc_file(temp_dir):
    """Create an older QC status file for testing file discrimination."""
    file_path = temp_dir / "data" / "QC_Status_Report_15AUG2025.json"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    old_data = [
        {
            "record_id": "UDS001",
            "redcap_event_name": "baseline_arm_1",
            "ptid": "UDS001",
            "qc_last_run": "15AUG2025",
            "qc_status": "0",
            "qc_results": "",
            "qc_run_by": "JT"
        }
    ]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(old_data, f, indent=2)
    
    return file_path


@pytest.fixture
def mock_requests_session():
    """Create a mock requests session for API testing."""
    session = Mock()
    
    # Default successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    mock_response.text = "[]"
    mock_response.raise_for_status.return_value = None
    
    session.post.return_value = mock_response
    session.get.return_value = mock_response
    
    return session


@pytest.fixture
def mock_redcap_api_response():
    """Mock REDCap API response data."""
    return {
        'export_response': [
            {
                "record_id": "UDS001",
                "redcap_event_name": "baseline_arm_1",
                "ptid": "UDS001",
                "qc_status_complete": "1",
                "qc_visit_date": "2025-08-01",
                "qc_last_run": "01AUG2025",
                "qc_notes": "Previous QC",
                "qc_status": "1",
                "qc_results": "Previous results",
                "qc_run_by": "JT"
            }
        ],
        'import_response': {
            'count': 3
        }
    }


@pytest.fixture
def change_tracker_data():
    """Sample data for testing change tracking."""
    old_data = [
        {
            "record_id": "UDS001",
            "redcap_event_name": "baseline_arm_1",
            "qc_status": "1",
            "qc_results": "Old results",
            "qc_last_run": "01AUG2025"
        }
    ]
    
    new_data = [
        {
            "record_id": "UDS001",
            "redcap_event_name": "baseline_arm_1",
            "qc_status": "2",
            "qc_results": "New results with audit trail",
            "qc_last_run": "15AUG2025"
        }
    ]
    
    return {"old_data": old_data, "new_data": new_data}


@pytest.fixture
def file_tracking_data():
    """Sample file tracking data for FileMonitor tests."""
    return {
        "QC_Status_Report_15AUG2025.json": {
            "path": "QC_Status_Report_15AUG2025.json",
            "hash": "abc123def456",
            "size": 1024,
            "modified_time": 1692105600.0,
            "processed_time": "2025-08-15T12:00:00",
            "records_count": 3
        }
    }


@pytest.fixture
def comprehensive_upload_log():
    """Sample comprehensive upload log for testing."""
    return {
        "upload_id": "upload_20250815_120000",
        "timestamp": "2025-08-15T12:00:00.000Z",
        "user_initials": "JT",
        "upload_type": "qc_status",
        "files_processed": [
            "QC_Status_Report_15AUG2025.json"
        ],
        "records_processed": 3,
        "dry_run": False,
        "force_upload": False,
        "operation_id": "op_12345",
        "changes": {
            "total_changes": 5,
            "records_affected": 3,
            "fields_changed": ["qc_status", "qc_results", "qc_last_run"]
        }
    }


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment variables."""
    test_env_vars = {
        "REDCAP_API_URL": "https://test-redcap.example.com/api/",
        "REDCAP_API_TOKEN": "test_token_123456789",
        "LOG_LEVEL": "DEBUG",
        "UPLOAD_READY_PATH": "./test_data",
        "BACKUP_LOG_PATH": "./test_backups"
    }
    
    for key, value in test_env_vars.items():
        monkeypatch.setenv(key, value)


class MockREDCapAPI:
    """Mock REDCap API for integration testing."""
    
    def __init__(self):
        self.records = []
        self.call_count = 0
        self.last_request = None
    
    def export_records(self, fields=None, events=None, format_type='json'):
        """Mock export records API call."""
        self.call_count += 1
        self.last_request = {
            'action': 'export_records',
            'fields': fields,
            'events': events,
            'format': format_type
        }
        return self.records
    
    def import_records(self, data, format_type='json', type_param='flat', overwrite='overwrite'):
        """Mock import records API call."""
        self.call_count += 1
        self.last_request = {
            'action': 'import_records',
            'data': data,
            'format': format_type,
            'type': type_param,
            'overwriteBehavior': overwrite
        }
        
        # Simulate successful import
        if isinstance(data, list):
            return {'count': len(data)}
        else:
            return {'count': 1}
    
    def reset(self):
        """Reset mock state."""
        self.call_count = 0
        self.last_request = None
        self.records = []


@pytest.fixture
def mock_redcap_api():
    """Create a mock REDCap API for testing."""
    return MockREDCapAPI()


# Test data patterns for file discrimination
@pytest.fixture
def test_file_patterns():
    """Common file naming patterns for testing file discrimination."""
    return {
        'valid_patterns': [
            'QC_Status_Report_21AUG2025.json',
            'QC_Status_Report_21AUG2025_120000.json',
            'QC_Status_Report_15JAN2025_235959.json',
            'QC_Status_Report_01DEC2024.json'
        ],
        'invalid_patterns': [
            'qc_status_report_21aug2025.json',  # Wrong case
            'QC_Status_Report_21AUG25.json',    # Wrong year format
            'QC_Status_21AUG2025.json',         # Missing "Report"
            'Status_Report_21AUG2025.json',     # Missing "QC"
            'QC_Status_Report_21AUG2025.txt',   # Wrong extension
            'QC_Status_Report_32AUG2025.json',  # Invalid date
            'QC_Status_Report_21XXX2025.json'   # Invalid month
        ]
    }
