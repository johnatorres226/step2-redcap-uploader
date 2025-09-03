"""Simple test to validate test setup."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_basic_setup():
    """Test basic setup is working."""
    assert True


def test_can_import_basic_modules():
    """Test that we can import basic modules."""
    try:
        from src.config.redcap_config import REDCapConfig
        from src.config.settings import Settings
        assert True
    except ImportError as e:
        assert False, f"Failed to import modules: {e}"


def test_can_create_basic_objects():
    """Test that we can create basic objects."""
    from src.config.redcap_config import REDCapConfig
    
    # Test creating a REDCapConfig with minimal data
    config = REDCapConfig(
        api_url="https://test.example.com/api/",
        api_token="test_token"
    )
    
    assert config.api_url == "https://test.example.com/api/"
    assert config.api_token == "test_token"
