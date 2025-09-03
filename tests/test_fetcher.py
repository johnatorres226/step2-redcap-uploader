"""Test suite for REDCapFetcher functionality."""

import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests
import sys

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.uploader.fetcher import REDCapFetcher


class TestREDCapFetcher:
    """Test REDCapFetcher class functionality."""
    
    def test_init(self, mock_redcap_config, test_logger):
        """Test REDCapFetcher initialization."""
        fetcher = REDCapFetcher(mock_redcap_config, test_logger)
        
        assert fetcher.config == mock_redcap_config
        assert fetcher.logger == test_logger
        assert fetcher.session is not None
        assert isinstance(fetcher.qc_status_fields, list)
        assert 'ptid' in fetcher.qc_status_fields
        assert 'qc_status' in fetcher.qc_status_fields
    
    def test_analyze_upload_data_valid_file(self, temp_dir, sample_qc_file, mock_redcap_config, test_logger):
        """Test analyzing valid upload data."""
        fetcher = REDCapFetcher(mock_redcap_config, test_logger)
        
        result = fetcher.analyze_upload_data(temp_dir / "data")
        
        assert result['success'] is True
        assert 'records_to_fetch' in result
        assert 'fields_needed' in result
        assert 'events_needed' in result
        assert len(result['records_to_fetch']) > 0
    
    def test_analyze_upload_data_no_files(self, temp_dir, mock_redcap_config, test_logger):
        """Test analyzing upload data when no files present."""
        fetcher = REDCapFetcher(mock_redcap_config, test_logger)
        
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        
        result = fetcher.analyze_upload_data(empty_dir)
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_analyze_upload_data_invalid_json(self, temp_dir, mock_redcap_config, test_logger):
        """Test analyzing upload data with invalid JSON."""
        fetcher = REDCapFetcher(mock_redcap_config, test_logger)
        
        # Create invalid JSON file
        invalid_file = temp_dir / "data" / "invalid.json"
        invalid_file.parent.mkdir(parents=True, exist_ok=True)
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json content")
        
        result = fetcher.analyze_upload_data(temp_dir / "data")
        
        assert result['success'] is False
        assert 'error' in result
    
    @patch('requests.Session.post')
    def test_fetch_qc_status_data_success(self, mock_post, mock_redcap_config, test_logger, sample_qc_data):
        """Test successful QC status data fetching."""
        fetcher = REDCapFetcher(mock_redcap_config, test_logger)
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_qc_data
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = fetcher.fetch_qc_status_data()
        
        assert result['success'] is True
        assert result['record_count'] == len(sample_qc_data)
        assert 'data' in result
        assert mock_post.called
    
    @patch('requests.Session.post')
    def test_fetch_qc_status_data_api_error(self, mock_post, mock_redcap_config, test_logger):
        """Test QC status data fetching with API error."""
        fetcher = REDCapFetcher(mock_redcap_config, test_logger)
        
        # Mock API error
        mock_post.side_effect = requests.RequestException("API Error")
        
        result = fetcher.fetch_qc_status_data()
        
        assert result['success'] is False
        assert 'error' in result
        assert 'API Error' in result['error']
    
    @patch('requests.Session.post')
    def test_fetch_qc_status_data_invalid_response(self, mock_post, mock_redcap_config, test_logger):
        """Test QC status data fetching with invalid response."""
        fetcher = REDCapFetcher(mock_redcap_config, test_logger)
        
        # Mock invalid response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid response"
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = fetcher.fetch_qc_status_data()
        
        assert result['success'] is False
        assert 'error' in result
    
    @patch('requests.Session.post')
    def test_fetch_qc_status_form_data(self, mock_post, mock_redcap_config, test_logger, sample_qc_data):
        """Test fetching QC status form data."""
        fetcher = REDCapFetcher(mock_redcap_config, test_logger)
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_qc_data[:2]  # Return first 2 records
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = fetcher.fetch_qc_status_form_data(
            record_ids=['UDS001', 'UDS002'],
            events=['baseline_arm_1']
        )
        
        assert result['success'] is True
        assert result['record_count'] == 2
        assert mock_post.called
        
        # Check that the API was called
        call_args = mock_post.call_args
        assert call_args is not None
    
    def test_save_fetched_data_to_output(self, temp_dir, mock_redcap_config, test_logger, sample_qc_data):
        """Test saving fetched data to output directory."""
        fetcher = REDCapFetcher(mock_redcap_config, test_logger)
        
        fetch_result = {
            'success': True,
            'data': sample_qc_data,
            'record_count': len(sample_qc_data),
            'timestamp': '2025-08-15T12:00:00'
        }
        
        output_dir = temp_dir / "output"
        result = fetcher.save_fetched_data_to_output(
            fetch_result,
            output_dir,
            "test_backup",
            create_subdir=True
        )
        
        assert result['success'] is True
        assert 'file_path' in result
        assert Path(result['file_path']).exists()
        
        # Verify file content
        with open(result['file_path'], 'r') as f:
            saved_data = json.load(f)
        assert saved_data == sample_qc_data
    
    def test_save_fetched_data_failed_fetch(self, temp_dir, mock_redcap_config, test_logger):
        """Test saving fetched data when fetch failed."""
        fetcher = REDCapFetcher(mock_redcap_config, test_logger)
        
        fetch_result = {
            'success': False,
            'error': 'Test error'
        }
        
        output_dir = temp_dir / "output"
        result = fetcher.save_fetched_data_to_output(
            fetch_result,
            output_dir,
            "test_backup"
        )
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_save_backup_files_to_directory(self, temp_dir, mock_redcap_config, test_logger, sample_qc_data):
        """Test saving backup files to directory."""
        fetcher = REDCapFetcher(mock_redcap_config, test_logger)
        
        fetch_result = {
            'success': True,
            'data': sample_qc_data,
            'record_count': len(sample_qc_data)
        }
        
        upload_data = sample_qc_data[:2]  # Subset for upload
        
        result = fetcher.save_backup_files_to_directory(
            fetch_result,
            temp_dir,
            upload_data
        )
        
        assert result['success'] is True
        assert 'files_created' in result
        assert len(result['files_created']) > 0
    
    def test_filter_qc_status_subset(self, mock_redcap_config, test_logger, sample_qc_data):
        """Test filtering QC status subset."""
        fetcher = REDCapFetcher(mock_redcap_config, test_logger)
        
        upload_data = [
            {"record_id": "UDS001", "redcap_event_name": "baseline_arm_1"},
            {"record_id": "UDS002", "redcap_event_name": "baseline_arm_1"}
        ]
        
        result = fetcher._filter_qc_status_subset(sample_qc_data, upload_data)
        
        assert len(result) == 2
        assert all(record['record_id'] in ['UDS001', 'UDS002'] for record in result)
    
    def test_get_unique_record_identifiers(self, mock_redcap_config, test_logger, sample_qc_data):
        """Test getting unique record identifiers."""
        fetcher = REDCapFetcher(mock_redcap_config, test_logger)
        
        identifiers = fetcher._get_unique_record_identifiers(sample_qc_data)
        
        assert 'record_ids' in identifiers
        assert 'events' in identifiers
        assert len(identifiers['record_ids']) == 3  # UDS001, UDS002, UDS003
        assert 'baseline_arm_1' in identifiers['events']
        assert 'followup_1_arm_1' in identifiers['events']
    
    def test_validate_api_response(self, mock_redcap_config, test_logger):
        """Test API response validation."""
        fetcher = REDCapFetcher(mock_redcap_config, test_logger)
        
        # Valid response
        valid_response = Mock()
        valid_response.status_code = 200
        valid_response.json.return_value = [{"record_id": "UDS001"}]
        
        assert fetcher._validate_api_response(valid_response) is True
        
        # Invalid status code
        invalid_response = Mock()
        invalid_response.status_code = 400
        invalid_response.raise_for_status.side_effect = requests.HTTPError("Bad request")
        
        assert fetcher._validate_api_response(invalid_response) is False
    
    def test_prepare_api_request(self, mock_redcap_config, test_logger):
        """Test API request preparation."""
        fetcher = REDCapFetcher(mock_redcap_config, test_logger)
        
        request_data = fetcher._prepare_api_request(
            content='record',
            format_type='json',
            records=['UDS001', 'UDS002'],
            fields=['ptid', 'qc_status'],
            events=['baseline_arm_1']
        )
        
        assert request_data['token'] == mock_redcap_config.api_token
        assert request_data['content'] == 'record'
        assert request_data['format'] == 'json'
        assert request_data['records'] == 'UDS001,UDS002'
        assert request_data['fields'] == 'ptid,qc_status'
        assert request_data['events'] == 'baseline_arm_1'
    
    @patch('requests.Session.post')
    def test_fetch_with_retry_logic(self, mock_post, mock_redcap_config, test_logger):
        """Test fetch with retry logic on temporary failures."""
        fetcher = REDCapFetcher(mock_redcap_config, test_logger)
        
        # First call fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.raise_for_status.side_effect = requests.HTTPError("Server error")
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = []
        mock_response_success.raise_for_status.return_value = None
        
        mock_post.side_effect = [mock_response_fail, mock_response_success]
        
        result = fetcher.fetch_qc_status_data(max_retries=2)
        
        assert result['success'] is True
        assert mock_post.call_count == 2
    
    def test_error_handling_malformed_data(self, temp_dir, mock_redcap_config, test_logger):
        """Test error handling with malformed data files."""
        fetcher = REDCapFetcher(mock_redcap_config, test_logger)
        
        # Create file with malformed data structure
        malformed_file = temp_dir / "data" / "malformed.json"
        malformed_file.parent.mkdir(parents=True, exist_ok=True)
        
        malformed_data = {
            "not_a_list": "should be list of records",
            "missing_fields": True
        }
        
        with open(malformed_file, 'w') as f:
            json.dump(malformed_data, f)
        
        result = fetcher.analyze_upload_data(temp_dir / "data")
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_large_dataset_handling(self, temp_dir, mock_redcap_config, test_logger):
        """Test handling of large datasets."""
        fetcher = REDCapFetcher(mock_redcap_config, test_logger)
        
        # Create large dataset
        large_dataset = []
        for i in range(1000):
            large_dataset.append({
                "record_id": f"UDS{i:04d}",
                "redcap_event_name": "baseline_arm_1",
                "ptid": f"UDS{i:04d}",
                "qc_status": "1"
            })
        
        large_file = temp_dir / "data" / "large_dataset.json"
        large_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(large_file, 'w') as f:
            json.dump(large_dataset, f)
        
        result = fetcher.analyze_upload_data(temp_dir / "data")
        
        assert result['success'] is True
        assert len(result['records_to_fetch']) == 1000
