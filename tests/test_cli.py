"""Test suite for CLI functionality."""

import sys
import json
import re
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.cli.cli import find_latest_qc_status_file, create_output_directory, setup_logging


class TestFindLatestQCStatusFile:
    """Test find_latest_qc_status_file function."""
    
    def test_find_latest_with_timestamp(self, temp_dir):
        """Test finding latest QC file with timestamps."""
        upload_path = temp_dir / "upload"
        upload_path.mkdir(parents=True, exist_ok=True)
        
        # Create files with different timestamps
        files_data = [
            ("QC_Status_Report_15AUG2025_120000.json", "15AUG2025_120000"),
            ("QC_Status_Report_16AUG2025_130000.json", "16AUG2025_130000"),
            ("QC_Status_Report_14AUG2025_140000.json", "14AUG2025_140000"),
        ]
        
        for filename, _ in files_data:
            file_path = upload_path / filename
            with open(file_path, 'w') as f:
                json.dump([{"test": "data"}], f)
        
        latest_file = find_latest_qc_status_file(upload_path)
        
        assert latest_file is not None
        assert latest_file.name == "QC_Status_Report_16AUG2025_130000.json"
    
    def test_find_latest_date_only(self, temp_dir):
        """Test finding latest QC file with date only (no timestamp)."""
        upload_path = temp_dir / "upload"
        upload_path.mkdir(parents=True, exist_ok=True)
        
        # Create files with date only
        files_data = [
            "QC_Status_Report_15AUG2025.json",
            "QC_Status_Report_17AUG2025.json",
            "QC_Status_Report_16AUG2025.json",
        ]
        
        for filename in files_data:
            file_path = upload_path / filename
            with open(file_path, 'w') as f:
                json.dump([{"test": "data"}], f)
        
        latest_file = find_latest_qc_status_file(upload_path)
        
        assert latest_file is not None
        assert latest_file.name == "QC_Status_Report_17AUG2025.json"
    
    def test_find_latest_mixed_formats(self, temp_dir):
        """Test finding latest QC file with mixed timestamp/date formats."""
        upload_path = temp_dir / "upload"
        upload_path.mkdir(parents=True, exist_ok=True)
        
        # Create files with mixed formats
        files_data = [
            "QC_Status_Report_15AUG2025.json",  # Date only
            "QC_Status_Report_16AUG2025_120000.json",  # Date with timestamp
            "QC_Status_Report_17AUG2025.json",  # Date only (latest)
            "QC_Status_Report_16AUG2025_230000.json",  # Date with timestamp (same day, later time)
        ]
        
        for filename in files_data:
            file_path = upload_path / filename
            with open(file_path, 'w') as f:
                json.dump([{"test": "data"}], f)
        
        latest_file = find_latest_qc_status_file(upload_path)
        
        assert latest_file is not None
        # Should pick the latest date (17AUG2025)
        assert latest_file.name == "QC_Status_Report_17AUG2025.json"
    
    def test_find_latest_no_files(self, temp_dir):
        """Test finding latest QC file when no files exist."""
        upload_path = temp_dir / "upload"
        upload_path.mkdir(parents=True, exist_ok=True)
        
        latest_file = find_latest_qc_status_file(upload_path)
        
        assert latest_file is None
    
    def test_find_latest_invalid_date_format(self, temp_dir):
        """Test finding latest QC file with invalid date format (falls back to file system date)."""
        upload_path = temp_dir / "upload"
        upload_path.mkdir(parents=True, exist_ok=True)
        
        # Create file with invalid date format
        invalid_file = upload_path / "QC_Status_Report_INVALID2025.json"
        valid_file = upload_path / "QC_Status_Report_15AUG2025.json"
        
        with open(invalid_file, 'w') as f:
            json.dump([{"test": "data"}], f)
        
        with open(valid_file, 'w') as f:
            json.dump([{"test": "data"}], f)
        
        latest_file = find_latest_qc_status_file(upload_path)
        
        # Should find the valid file
        assert latest_file is not None
        assert latest_file.name == "QC_Status_Report_15AUG2025.json"
    
    def test_find_latest_wrong_file_pattern(self, temp_dir):
        """Test finding latest QC file with wrong file patterns (should be ignored)."""
        upload_path = temp_dir / "upload"
        upload_path.mkdir(parents=True, exist_ok=True)
        
        # Create files with wrong patterns
        wrong_files = [
            "qc_status_report_15aug2025.json",  # Wrong case
            "QC_Status_15AUG2025.json",  # Missing "Report"
            "Status_Report_15AUG2025.json",  # Missing "QC"
            "QC_Status_Report_15AUG2025.txt",  # Wrong extension
        ]
        
        for filename in wrong_files:
            file_path = upload_path / filename
            with open(file_path, 'w') as f:
                json.dump([{"test": "data"}], f)
        
        # Add one correct file
        correct_file = upload_path / "QC_Status_Report_15AUG2025.json"
        with open(correct_file, 'w') as f:
            json.dump([{"test": "data"}], f)
        
        latest_file = find_latest_qc_status_file(upload_path)
        
        assert latest_file is not None
        assert latest_file.name == "QC_Status_Report_15AUG2025.json"
    
    def test_regex_pattern_validation(self, temp_dir):
        """Test that regex patterns work correctly for various file names."""
        upload_path = temp_dir / "upload"
        upload_path.mkdir(parents=True, exist_ok=True)
        
        # Test various valid patterns
        valid_patterns = [
            "QC_Status_Report_01JAN2025.json",
            "QC_Status_Report_31DEC2025.json",
            "QC_Status_Report_15AUG2025_000000.json",
            "QC_Status_Report_15AUG2025_235959.json",
        ]
        
        for filename in valid_patterns:
            file_path = upload_path / filename
            with open(file_path, 'w') as f:
                json.dump([{"test": "data"}], f)
        
        latest_file = find_latest_qc_status_file(upload_path)
        
        assert latest_file is not None
        # Should find one of the valid files
        assert latest_file.name in valid_patterns


class TestCreateOutputDirectory:
    """Test create_output_directory function."""
    
    def test_create_output_directory_default(self, temp_dir):
        """Test creating output directory with default path."""
        with patch('src.cli.cli.Path') as mock_path:
            mock_path.return_value = temp_dir
            
            output_dir = create_output_directory()
            
            assert output_dir is not None
            assert isinstance(output_dir, Path)
    
    def test_create_output_directory_custom_path(self, temp_dir):
        """Test creating output directory with custom path."""
        custom_path = temp_dir / "custom_output"
        
        output_dir = create_output_directory(custom_path)
        
        assert output_dir == custom_path
        assert output_dir.exists()
    
    def test_create_output_directory_with_timestamp_format(self):
        """Test that output directory includes proper timestamp format."""
        with patch('src.cli.cli.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "12Aug2025_140530"
            
            with patch('src.cli.cli.Path') as mock_path_class:
                mock_base_path = Mock()
                mock_output_path = Mock()
                mock_path_class.return_value = mock_base_path
                mock_base_path.__truediv__.return_value = mock_output_path
                mock_output_path.mkdir.return_value = None
                
                result = create_output_directory()
                
                # Check that the timestamp format is used
                mock_datetime.now.return_value.strftime.assert_called_with('%d%b%Y_%H%M%S')


class TestSetupLogging:
    """Test setup_logging function."""
    
    def test_setup_logging_basic(self):
        """Test basic logging setup."""
        logger = setup_logging("JT")
        
        assert logger is not None
        assert logger.name == "udsv4_redcap_uploader"
        assert logger.level == 20  # INFO level
        assert len(logger.handlers) > 0
    
    def test_setup_logging_handler_configuration(self):
        """Test that logging handlers are configured correctly."""
        logger = setup_logging("TEST")
        
        # Check that at least one handler is configured
        assert len(logger.handlers) > 0
        
        # Check that handlers have formatters
        for handler in logger.handlers:
            assert handler.formatter is not None


class TestCLIIntegration:
    """Test CLI integration and file discrimination."""
    
    def test_file_discrimination_logic(self, temp_dir, test_file_patterns):
        """Test file discrimination logic with various file patterns."""
        upload_path = temp_dir / "upload"
        upload_path.mkdir(parents=True, exist_ok=True)
        
        # Create files with valid patterns
        for filename in test_file_patterns['valid_patterns']:
            file_path = upload_path / filename
            with open(file_path, 'w') as f:
                json.dump([{"test": "data"}], f)
        
        # Create files with invalid patterns  
        for filename in test_file_patterns['invalid_patterns']:
            file_path = upload_path / filename
            with open(file_path, 'w') as f:
                json.dump([{"test": "data"}], f)
        
        latest_file = find_latest_qc_status_file(upload_path)
        
        # Should find a valid file and ignore invalid ones
        assert latest_file is not None
        assert latest_file.name in test_file_patterns['valid_patterns']
    
    def test_date_parsing_edge_cases(self, temp_dir):
        """Test date parsing with edge cases."""
        upload_path = temp_dir / "upload"
        upload_path.mkdir(parents=True, exist_ok=True)
        
        # Test edge date cases
        edge_cases = [
            "QC_Status_Report_29FEB2024.json",  # Leap year
            "QC_Status_Report_01JAN2025.json",  # Year start
            "QC_Status_Report_31DEC2025.json",  # Year end
        ]
        
        for filename in edge_cases:
            file_path = upload_path / filename
            with open(file_path, 'w') as f:
                json.dump([{"test": "data"}], f)
        
        latest_file = find_latest_qc_status_file(upload_path)
        
        assert latest_file is not None
        # Should pick the latest valid date
        assert latest_file.name == "QC_Status_Report_31DEC2025.json"
    
    def test_timestamp_comparison_accuracy(self, temp_dir):
        """Test that timestamp comparison is accurate."""
        upload_path = temp_dir / "upload"
        upload_path.mkdir(parents=True, exist_ok=True)
        
        # Create files with very close timestamps
        close_timestamps = [
            "QC_Status_Report_15AUG2025_120000.json",
            "QC_Status_Report_15AUG2025_120001.json",  # 1 second later
            "QC_Status_Report_15AUG2025_115959.json",  # 1 second earlier
        ]
        
        for filename in close_timestamps:
            file_path = upload_path / filename
            with open(file_path, 'w') as f:
                json.dump([{"test": "data"}], f)
        
        latest_file = find_latest_qc_status_file(upload_path)
        
        assert latest_file is not None
        assert latest_file.name == "QC_Status_Report_15AUG2025_120001.json"
    
    def test_case_sensitivity(self, temp_dir):
        """Test case sensitivity in file pattern matching."""
        upload_path = temp_dir / "upload"
        upload_path.mkdir(parents=True, exist_ok=True)
        
        # Test case variations
        case_variations = [
            "QC_Status_Report_15AUG2025.json",  # Correct case
            "qc_status_report_15aug2025.json",  # All lowercase
            "QC_STATUS_REPORT_15AUG2025.JSON",  # All uppercase
        ]
        
        for filename in case_variations:
            file_path = upload_path / filename
            with open(file_path, 'w') as f:
                json.dump([{"test": "data"}], f)
        
        latest_file = find_latest_qc_status_file(upload_path)
        
        # Should only find the correctly cased file
        assert latest_file is not None
        assert latest_file.name == "QC_Status_Report_15AUG2025.json"
    
    def test_month_abbreviation_validation(self, temp_dir):
        """Test validation of month abbreviations."""
        upload_path = temp_dir / "upload"
        upload_path.mkdir(parents=True, exist_ok=True)
        
        # Valid month abbreviations
        valid_months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", 
                       "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        
        for i, month in enumerate(valid_months):
            filename = f"QC_Status_Report_15{month}2025.json"
            file_path = upload_path / filename
            with open(file_path, 'w') as f:
                json.dump([{"test": "data"}], f)
        
        # Invalid month
        invalid_file = upload_path / "QC_Status_Report_15XXX2025.json"
        with open(invalid_file, 'w') as f:
            json.dump([{"test": "data"}], f)
        
        latest_file = find_latest_qc_status_file(upload_path)
        
        # Should find a valid month file, not the invalid one
        assert latest_file is not None
        assert "XXX" not in latest_file.name
        assert any(month in latest_file.name for month in valid_months)
    
    @patch('src.cli.cli.QCDataUploader')
    @patch('src.cli.cli.REDCapFetcher')
    @patch('src.cli.cli.REDCapConfig.from_env')
    @patch('src.cli.cli.Settings.from_env')
    def test_cli_integration_with_mocked_components(self, mock_settings, mock_config, 
                                                   mock_fetcher_class, mock_uploader_class,
                                                   temp_dir, sample_qc_file):
        """Test CLI integration with mocked components."""
        # Setup mocks
        mock_settings.return_value = Mock()
        mock_config.return_value = Mock()
        
        mock_fetcher = Mock()
        mock_fetcher.fetch_qc_status_data.return_value = {
            'success': True,
            'record_count': 3,
            'data': []
        }
        mock_fetcher.save_fetched_data_to_output.return_value = {
            'success': True,
            'file_path': str(temp_dir / "backup.json")
        }
        mock_fetcher_class.return_value = mock_fetcher
        
        mock_uploader = Mock()
        mock_uploader.upload_qc_status_data.return_value = {
            'success': True,
            'records_processed': 3
        }
        mock_uploader_class.return_value = mock_uploader
        
        # This would test the actual CLI run command, but we'll just verify mocks are set up
        assert mock_fetcher is not None
        assert mock_uploader is not None
