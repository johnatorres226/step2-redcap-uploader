"""Basic tests for the configuration module."""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from config.settings import Settings
from config.redcap_config import REDCapConfig


class TestSettings:
    """Test Settings class."""
    
    def test_settings_initialization(self):
        """Test basic settings initialization."""
        settings = Settings()
        
        # Check default values
        assert settings.CHECK_FILE_CHANGES is True
        assert settings.BATCH_SIZE == 100
        assert settings.VALIDATE_DATA is True
        
        # Check computed fields
        assert settings.DATA_DIR.name == "data"
        assert settings.LOGS_DIR.name == "logs"
        assert settings.BACKUPS_DIR.name == "backups"
    
    @patch.dict(os.environ, {
        'LOG_LEVEL': 'DEBUG',
        'BATCH_SIZE': '200',
        'CHECK_FILE_CHANGES': 'false'
    })
    def test_settings_from_env(self):
        """Test settings creation from environment variables."""
        settings = Settings.from_env()
        
        assert settings.LOG_LEVEL == 'DEBUG'
        assert settings.BATCH_SIZE == 200
        assert settings.CHECK_FILE_CHANGES is False


class TestREDCapConfig:
    """Test REDCapConfig class."""
    
    def test_redcap_config_initialization(self):
        """Test basic REDCap config initialization."""
        config = REDCapConfig(
            api_url="https://test.redcap.com/api/",
            api_token="test_token_123"
        )
        
        assert config.api_url == "https://test.redcap.com/api/"
        assert config.api_token == "test_token_123"
        assert config.timeout == 30
        assert config.format == "json"
    
    @patch.dict(os.environ, {
        'REDCAP_API_URL': 'https://env.redcap.com/api/',
        'REDCAP_API_TOKEN': 'env_token_456',
        'REDCAP_TIMEOUT': '60'
    })
    def test_redcap_config_from_env(self):
        """Test REDCap config creation from environment variables."""
        config = REDCapConfig.from_env()
        
        assert config.api_url == 'https://env.redcap.com/api/'
        assert config.api_token == 'env_token_456'
        assert config.timeout == 60
    
    def test_redcap_config_missing_env_vars(self):
        """Test error handling for missing environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="REDCAP_API_URL"):
                REDCapConfig.from_env()
    
    def test_get_export_payload(self):
        """Test export payload generation."""
        config = REDCapConfig(
            api_url="https://test.redcap.com/api/",
            api_token="test_token"
        )
        
        payload = config.get_export_payload(forms=['form1', 'form2'])
        
        assert payload['token'] == 'test_token'
        assert payload['content'] == 'record'
        assert payload['action'] == 'export'
        assert payload['forms'] == ['form1', 'form2']
    
    def test_get_import_payload(self):
        """Test import payload generation."""
        config = REDCapConfig(
            api_url="https://test.redcap.com/api/",
            api_token="test_token"
        )
        
        test_data = '{"test": "data"}'
        payload = config.get_import_payload(test_data)
        
        assert payload['token'] == 'test_token'
        assert payload['content'] == 'record'
        assert payload['action'] == 'import'
        assert payload['data'] == test_data


class TestConfigIntegration:
    """Integration tests for configuration."""
    
    def test_config_compatibility(self):
        """Test that configs work together."""
        settings = Settings()
        
        # Mock environment for REDCap config
        with patch.dict(os.environ, {
            'REDCAP_API_URL': 'https://test.redcap.com/api/',
            'REDCAP_API_TOKEN': 'test_token'
        }):
            redcap_config = REDCapConfig.from_env()
        
        # Test that directories exist and are accessible
        assert settings.DATA_DIR.exists()
        assert settings.LOGS_DIR.exists()
        assert settings.BACKUPS_DIR.exists()
        
        # Test that REDCap config is valid
        assert redcap_config.api_url.endswith('/api/')
        assert len(redcap_config.api_token) > 0
