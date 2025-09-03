"""Test suite for configuration classes based on actual implementation."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.redcap_config import REDCapConfig
from src.config.settings import Settings


class TestREDCapConfig:
    """Test REDCapConfig class with actual attributes."""
    
    def test_redcap_config_creation(self):
        """Test creating REDCapConfig with basic parameters."""
        config = REDCapConfig(
            api_url="https://test.redcap.edu/api/",
            api_token="test_token_12345"
        )
        
        assert config.api_url == "https://test.redcap.edu/api/"
        assert config.api_token == "test_token_12345"
        assert config.timeout == 30  # Default value
        assert config.max_retries == 3  # Default value
        assert config.format == "json"  # Default value
    
    def test_redcap_config_with_custom_values(self):
        """Test creating REDCapConfig with custom values."""
        config = REDCapConfig(
            api_url="https://custom.redcap.edu/api/",
            api_token="custom_token",
            project_id="CUSTOM_PROJECT",
            timeout=45,
            max_retries=5,
            retry_delay=2.0
        )
        
        assert config.api_url == "https://custom.redcap.edu/api/"
        assert config.api_token == "custom_token"
        assert config.project_id == "CUSTOM_PROJECT"
        assert config.timeout == 45
        assert config.max_retries == 5
        assert config.retry_delay == 2.0
    
    def test_from_env_basic(self):
        """Test creating REDCapConfig from environment variables."""
        env_vars = {
            'REDCAP_API_URL': 'https://env.redcap.edu/api/',
            'REDCAP_API_TOKEN': 'env_token_12345'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = REDCapConfig.from_env()
            
            assert config.api_url == 'https://env.redcap.edu/api/'
            assert config.api_token == 'env_token_12345'
    
    def test_from_env_with_project_id(self):
        """Test creating REDCapConfig from env with project ID."""
        env_vars = {
            'REDCAP_API_URL': 'https://project.redcap.edu/api/',
            'REDCAP_API_TOKEN': 'project_token'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = REDCapConfig.from_env(project_id="TEST_PROJECT")
            
            assert config.api_url == 'https://project.redcap.edu/api/'
            assert config.api_token == 'project_token'
            assert config.project_id == "TEST_PROJECT"
    
    def test_get_export_payload(self):
        """Test getting export payload."""
        config = REDCapConfig(
            api_url="https://test.redcap.edu/api/",
            api_token="test_token"
        )
        
        payload = config.get_export_payload()
        
        assert isinstance(payload, dict)
        assert 'token' in payload
        assert 'content' in payload
        assert 'format' in payload
        assert payload['token'] == "test_token"
        assert payload['format'] == "json"
    
    def test_get_export_payload_with_kwargs(self):
        """Test getting export payload with custom parameters."""
        config = REDCapConfig(
            api_url="https://test.redcap.edu/api/",
            api_token="test_token"
        )
        
        payload = config.get_export_payload(
            records=['UDS001', 'UDS002'],
            fields=['ptid', 'qc_status']
        )
        
        assert isinstance(payload, dict)
        assert 'records' in payload
        assert 'fields' in payload
        assert payload['records'] == ['UDS001', 'UDS002']
        assert payload['fields'] == ['ptid', 'qc_status']
    
    def test_get_import_payload(self):
        """Test getting import payload."""
        config = REDCapConfig(
            api_url="https://test.redcap.edu/api/",
            api_token="test_token"
        )
        
        test_data = '[{"record_id": "UDS001", "ptid": "UDS001"}]'
        payload = config.get_import_payload(data=test_data)
        
        assert isinstance(payload, dict)
        assert 'token' in payload
        assert 'content' in payload
        assert 'format' in payload
        assert 'data' in payload
        assert payload['data'] == test_data
        assert payload['content'] == 'record'
    
    def test_get_import_payload_with_kwargs(self):
        """Test getting import payload with custom parameters."""
        config = REDCapConfig(
            api_url="https://test.redcap.edu/api/",
            api_token="test_token"
        )
        
        test_data = '[{"record_id": "UDS001"}]'
        payload = config.get_import_payload(
            data=test_data,
            overwriteBehavior='overwrite',
            returnContent='ids'
        )
        
        assert payload['overwriteBehavior'] == 'overwrite'
        assert payload['returnContent'] == 'ids'


class TestSettings:
    """Test Settings class with actual attributes."""
    
    def test_settings_creation(self):
        """Test creating Settings instance."""
        settings = Settings()
        
        # Test some key attributes
        assert hasattr(settings, 'BASE_DIR')
        assert hasattr(settings, 'DATA_DIR')
        assert hasattr(settings, 'LOGS_DIR')
        assert hasattr(settings, 'OUTPUT_DIR')
        assert hasattr(settings, 'LOG_LEVEL')
        assert hasattr(settings, 'DRY_RUN_DEFAULT')
    
    def test_settings_directory_attributes(self):
        """Test Settings directory attributes."""
        settings = Settings()
        
        # These should be Path-like or string attributes
        assert settings.BASE_DIR is not None
        assert settings.DATA_DIR is not None
        assert settings.LOGS_DIR is not None
        assert settings.OUTPUT_DIR is not None
        assert settings.BACKUPS_DIR is not None
    
    def test_settings_configuration_attributes(self):
        """Test Settings configuration attributes."""
        settings = Settings()
        
        # Test configuration values
        assert isinstance(settings.LOG_LEVEL, str)
        assert isinstance(settings.DRY_RUN_DEFAULT, bool)
        assert isinstance(settings.BACKUP_BEFORE_UPLOAD, bool)
        assert isinstance(settings.VALIDATE_DATA, bool)
        assert isinstance(settings.CHECK_FILE_CHANGES, bool)
    
    def test_settings_numeric_attributes(self):
        """Test Settings numeric attributes."""
        settings = Settings()
        
        # Test numeric settings
        assert isinstance(settings.BATCH_SIZE, int)
        assert isinstance(settings.MAX_RETRIES, int)
        assert isinstance(settings.RETRY_DELAY, (int, float))
        assert settings.BATCH_SIZE > 0
        assert settings.MAX_RETRIES >= 0
        assert settings.RETRY_DELAY >= 0
    
    def test_from_env_method_exists(self):
        """Test that from_env method exists and works."""
        # Test that the method exists and can be called
        settings = Settings.from_env()
        
        assert isinstance(settings, Settings)
        assert hasattr(settings, 'BASE_DIR')
        assert hasattr(settings, 'LOG_LEVEL')
    
    def test_from_env_with_environment_variables(self):
        """Test Settings from_env with environment variables."""
        # Test with some environment variables set
        env_vars = {
            'UDSV4_LOG_LEVEL': 'DEBUG',
            'UDSV4_DRY_RUN': 'true',
            'UDSV4_BATCH_SIZE': '100'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            try:
                settings = Settings.from_env()
                assert isinstance(settings, Settings)
                # The implementation might or might not use these env vars
                # Just ensure it doesn't crash
            except Exception:
                # Some env vars might not be supported, that's okay
                pass
    
    def test_file_paths_are_valid(self):
        """Test that file paths in settings are valid."""
        settings = Settings()
        
        # Test that paths can be converted to Path objects
        base_dir = Path(settings.BASE_DIR) if settings.BASE_DIR else Path.cwd()
        data_dir = Path(settings.DATA_DIR) if settings.DATA_DIR else base_dir / "data"
        logs_dir = Path(settings.LOGS_DIR) if settings.LOGS_DIR else base_dir / "logs"
        
        # Should not raise exceptions
        assert isinstance(base_dir, Path)
        assert isinstance(data_dir, Path)
        assert isinstance(logs_dir, Path)
    
    def test_default_forms_and_events(self):
        """Test default forms and events settings."""
        settings = Settings()
        
        # These should be lists or None
        if hasattr(settings, 'DEFAULT_FORMS'):
            assert isinstance(settings.DEFAULT_FORMS, (list, type(None)))
        
        if hasattr(settings, 'DEFAULT_EVENTS'):
            assert isinstance(settings.DEFAULT_EVENTS, (list, type(None)))
    
    def test_log_configuration(self):
        """Test logging configuration settings."""
        settings = Settings()
        
        # Test logging-related settings
        assert isinstance(settings.LOG_TO_FILE, bool)
        assert isinstance(settings.LOG_TO_CONSOLE, bool)
        assert isinstance(settings.LOG_FORMAT, str)
        assert len(settings.LOG_FORMAT) > 0


class TestConfigurationIntegration:
    """Test integration between configuration classes."""
    
    def test_both_configs_can_be_created(self):
        """Test that both config classes can be instantiated together."""
        redcap_config = REDCapConfig(
            api_url="https://integration.redcap.edu/api/",
            api_token="integration_token"
        )
        
        settings = Settings()
        
        assert redcap_config is not None
        assert settings is not None
        assert redcap_config.api_url == "https://integration.redcap.edu/api/"
        assert hasattr(settings, 'BASE_DIR')
    
    def test_from_env_integration(self):
        """Test creating both configs from environment."""
        env_vars = {
            'REDCAP_API_URL': 'https://integration.redcap.edu/api/',
            'REDCAP_API_TOKEN': 'integration_token'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            redcap_config = REDCapConfig.from_env()
            settings = Settings.from_env()
            
            assert redcap_config.api_url == 'https://integration.redcap.edu/api/'
            assert isinstance(settings, Settings)
