"""Test suite for QCDataUploader functionality."""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.uploader.uploader import QCDataUploader


class TestQCDataUploader:
    """Test QCDataUploader class functionality."""
    
    def test_init(self, mock_redcap_config, test_settings, test_logger):
        """Test QCDataUploader initialization."""
        uploader = QCDataUploader(mock_redcap_config, test_settings, test_logger)
        
        assert uploader.config == mock_redcap_config
        assert uploader.settings == test_settings
        assert uploader.logger == test_logger
        assert uploader.session is not None
        assert uploader.fetcher is not None
        assert uploader.data_processor is not None
        assert uploader.change_tracker is not None
        assert uploader.file_monitor is not None
    
    @patch('src.uploader.uploader.QCDataUploader._upload_to_redcap')
    @patch('src.uploader.fetcher.REDCapFetcher.fetch_qc_status_data')
    def test_upload_qc_status_data_success(self, mock_fetch, mock_upload, temp_dir, sample_qc_file, 
                                          mock_redcap_config, test_settings, test_logger, sample_qc_data):
        """Test successful QC status data upload."""
        uploader = QCDataUploader(mock_redcap_config, test_settings, test_logger)
        
        # Mock fetch response
        mock_fetch.return_value = {
            'success': True,
            'data': sample_qc_data[:1],  # Return one record
            'record_count': 1
        }
        
        # Mock upload response
        mock_upload.return_value = {
            'success': True,
            'count': 3,
            'receipt': {'count': 3}
        }
        
        result = uploader.upload_qc_status_data(
            upload_path=temp_dir / "data",
            initials="JT",
            dry_run=False,
            force_upload=False
        )
        
        assert result['success'] is True
        assert 'records_processed' in result
        assert mock_fetch.called
        assert mock_upload.called
    
    @patch('src.uploader.fetcher.REDCapFetcher.fetch_qc_status_data')
    def test_upload_qc_status_data_dry_run(self, mock_fetch, temp_dir, sample_qc_file,
                                          mock_redcap_config, test_settings, test_logger, sample_qc_data):
        """Test QC status data upload in dry run mode."""
        uploader = QCDataUploader(mock_redcap_config, test_settings, test_logger)
        
        # Mock fetch response
        mock_fetch.return_value = {
            'success': True,
            'data': sample_qc_data,
            'record_count': len(sample_qc_data)
        }
        
        result = uploader.upload_qc_status_data(
            upload_path=temp_dir / "data",
            initials="JT",
            dry_run=True,
            force_upload=False
        )
        
        assert result['success'] is True
        assert result['dry_run'] is True
        assert 'validation_passed' in result
        assert mock_fetch.called
    
    def test_upload_qc_status_data_no_files(self, temp_dir, mock_redcap_config, test_settings, test_logger):
        """Test upload when no files are found."""
        uploader = QCDataUploader(mock_redcap_config, test_settings, test_logger)
        
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        
        result = uploader.upload_qc_status_data(
            upload_path=empty_dir,
            initials="JT",
            dry_run=False,
            force_upload=False
        )
        
        assert result['success'] is False
        assert 'error' in result
        assert 'No QC Status Report files found' in result['error']
    
    @patch('src.uploader.fetcher.REDCapFetcher.fetch_qc_status_data')
    def test_upload_qc_status_data_fetch_failure(self, mock_fetch, temp_dir, sample_qc_file,
                                                 mock_redcap_config, test_settings, test_logger):
        """Test upload when fetching current data fails."""
        uploader = QCDataUploader(mock_redcap_config, test_settings, test_logger)
        
        # Mock fetch failure
        mock_fetch.return_value = {
            'success': False,
            'error': 'API connection failed'
        }
        
        result = uploader.upload_qc_status_data(
            upload_path=temp_dir / "data",
            initials="JT",
            dry_run=False,
            force_upload=False
        )
        
        assert result['success'] is False
        assert 'error' in result
        assert mock_fetch.called
    
    @patch('requests.Session.post')
    def test_upload_to_redcap_success(self, mock_post, mock_redcap_config, test_settings, test_logger, sample_qc_data):
        """Test successful upload to REDCap API."""
        uploader = QCDataUploader(mock_redcap_config, test_settings, test_logger)
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'count': 3}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = uploader._upload_to_redcap(sample_qc_data)
        
        assert result['success'] is True
        assert result['count'] == 3
        assert mock_post.called
    
    @patch('requests.Session.post')
    def test_upload_to_redcap_api_error(self, mock_post, mock_redcap_config, test_settings, test_logger, sample_qc_data):
        """Test upload to REDCap with API error."""
        uploader = QCDataUploader(mock_redcap_config, test_settings, test_logger)
        
        # Mock API error
        mock_post.side_effect = requests.RequestException("Upload failed")
        
        result = uploader._upload_to_redcap(sample_qc_data)
        
        assert result['success'] is False
        assert 'error' in result
        assert 'Upload failed' in result['error']
    
    def test_load_and_validate_upload_data(self, temp_dir, sample_qc_file, mock_redcap_config, test_settings, test_logger):
        """Test loading and validating upload data."""
        uploader = QCDataUploader(mock_redcap_config, test_settings, test_logger)
        
        result = uploader._load_and_validate_upload_data(temp_dir / "data")
        
        assert result['success'] is True
        assert 'data' in result
        assert 'file_path' in result
        assert len(result['data']) > 0
    
    def test_load_and_validate_upload_data_invalid(self, temp_dir, mock_redcap_config, test_settings, test_logger):
        """Test loading invalid upload data."""
        uploader = QCDataUploader(mock_redcap_config, test_settings, test_logger)
        
        # Create invalid JSON file
        invalid_file = temp_dir / "data" / "QC_Status_Report_invalid.json"
        invalid_file.parent.mkdir(parents=True, exist_ok=True)
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json")
        
        result = uploader._load_and_validate_upload_data(temp_dir / "data")
        
        assert result['success'] is False
        assert 'error' in result
    
    @patch('src.uploader.fetcher.REDCapFetcher.fetch_qc_status_data')
    def test_check_for_duplicates(self, mock_fetch, mock_redcap_config, test_settings, test_logger, sample_qc_data):
        """Test duplicate checking functionality."""
        uploader = QCDataUploader(mock_redcap_config, test_settings, test_logger)
        
        # Mock current data with same qc_last_run
        current_data = [
            {
                "record_id": "UDS001",
                "redcap_event_name": "baseline_arm_1",
                "qc_last_run": "15AUG2025"
            }
        ]
        
        upload_data = [
            {
                "record_id": "UDS001",
                "redcap_event_name": "baseline_arm_1",
                "qc_last_run": "15AUG2025"  # Same as current
            }
        ]
        
        duplicates = uploader._check_for_duplicates(current_data, upload_data)
        
        assert len(duplicates) == 1
        assert duplicates[0]['record_id'] == "UDS001"
    
    def test_add_audit_trail(self, mock_redcap_config, test_settings, test_logger, sample_qc_data):
        """Test adding audit trail to upload data."""
        uploader = QCDataUploader(mock_redcap_config, test_settings, test_logger)
        
        current_data = [
            {
                "record_id": "UDS001",
                "redcap_event_name": "baseline_arm_1",
                "qc_results": "Previous results"
            }
        ]
        
        upload_data = [
            {
                "record_id": "UDS001",
                "redcap_event_name": "baseline_arm_1",
                "qc_results": "New results"
            }
        ]
        
        result = uploader._add_audit_trail(upload_data, current_data, "JT")
        
        assert len(result) == 1
        assert "Previous results" in result[0]['qc_results']
        assert "New results" in result[0]['qc_results']
        assert "JT" in result[0]['qc_results']
    
    def test_create_output_files(self, temp_dir, mock_redcap_config, test_settings, test_logger, sample_qc_data):
        """Test creating output files."""
        uploader = QCDataUploader(mock_redcap_config, test_settings, test_logger)
        
        upload_result = {
            'success': True,
            'count': 3,
            'receipt': {'count': 3}
        }
        
        output_dir = temp_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        result = uploader._create_output_files(
            upload_data=sample_qc_data,
            upload_result=upload_result,
            output_dir=output_dir,
            initials="JT"
        )
        
        assert result['success'] is True
        assert 'receipt_file' in result
        assert 'uploaded_data_file' in result
        assert Path(result['receipt_file']).exists()
        assert Path(result['uploaded_data_file']).exists()
    
    def test_validate_upload_data_structure(self, mock_redcap_config, test_settings, test_logger, sample_qc_data):
        """Test validating upload data structure."""
        uploader = QCDataUploader(mock_redcap_config, test_settings, test_logger)
        
        # Valid data
        result = uploader._validate_upload_data_structure(sample_qc_data)
        assert result['valid'] is True
        
        # Invalid data - missing required fields
        invalid_data = [{"record_id": "UDS001"}]  # Missing other required fields
        result = uploader._validate_upload_data_structure(invalid_data)
        assert result['valid'] is False
        assert 'errors' in result
    
    @patch('src.uploader.uploader.QCDataUploader._upload_to_redcap')
    @patch('src.uploader.fetcher.REDCapFetcher.fetch_qc_status_data')
    def test_force_upload_mode(self, mock_fetch, mock_upload, temp_dir, sample_qc_file,
                              mock_redcap_config, test_settings, test_logger, sample_qc_data):
        """Test upload with force mode enabled."""
        uploader = QCDataUploader(mock_redcap_config, test_settings, test_logger)
        
        # Mock current data with same qc_last_run (would normally be duplicate)
        current_data = [
            {
                "record_id": "UDS001",
                "redcap_event_name": "baseline_arm_1",
                "qc_last_run": "15AUG2025"
            }
        ]
        
        mock_fetch.return_value = {
            'success': True,
            'data': current_data,
            'record_count': 1
        }
        
        mock_upload.return_value = {
            'success': True,
            'count': 3,
            'receipt': {'count': 3}
        }
        
        result = uploader.upload_qc_status_data(
            upload_path=temp_dir / "data",
            initials="JT",
            dry_run=False,
            force_upload=True  # Force upload even with duplicates
        )
        
        assert result['success'] is True
        assert mock_upload.called  # Should still upload with force=True
    
    def test_error_handling_in_upload_process(self, temp_dir, mock_redcap_config, test_settings, test_logger):
        """Test error handling during upload process."""
        uploader = QCDataUploader(mock_redcap_config, test_settings, test_logger)
        
        # Test with non-existent directory
        non_existent_dir = temp_dir / "does_not_exist"
        
        result = uploader.upload_qc_status_data(
            upload_path=non_existent_dir,
            initials="JT",
            dry_run=False,
            force_upload=False
        )
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_output_directory_creation(self, temp_dir, mock_redcap_config, test_settings, test_logger):
        """Test custom output directory creation."""
        uploader = QCDataUploader(mock_redcap_config, test_settings, test_logger)
        
        custom_output_dir = temp_dir / "custom_output"
        
        with patch.object(uploader, '_load_and_validate_upload_data') as mock_load:
            mock_load.return_value = {
                'success': False,
                'error': 'No files found'
            }
            
            result = uploader.upload_qc_status_data(
                upload_path=temp_dir / "data",
                initials="JT",
                dry_run=False,
                force_upload=False,
                custom_output_dir=custom_output_dir
            )
            
            # Directory should be created even if upload fails
            assert custom_output_dir.exists()
    
    def test_large_dataset_upload(self, temp_dir, mock_redcap_config, test_settings, test_logger):
        """Test uploading large datasets."""
        uploader = QCDataUploader(mock_redcap_config, test_settings, test_logger)
        
        # Create large dataset
        large_dataset = []
        for i in range(500):
            large_dataset.append({
                "record_id": f"UDS{i:04d}",
                "redcap_event_name": "baseline_arm_1",
                "ptid": f"UDS{i:04d}",
                "qc_status": "1",
                "qc_last_run": "15AUG2025",
                "qc_results": f"Results for record {i}",
                "qc_run_by": "JT"
            })
        
        large_file = temp_dir / "data" / "QC_Status_Report_large.json"
        large_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(large_file, 'w') as f:
            json.dump(large_dataset, f)
        
        # Test validation of large dataset
        result = uploader._validate_upload_data_structure(large_dataset)
        
        assert result['valid'] is True
        # Should handle large datasets without issues
