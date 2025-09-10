"""REDCap API configuration and utilities."""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class REDCapConfig:
    """REDCap API configuration."""
    
    api_url: str
    api_token: str
    project_id: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # API request defaults
    format: str = "json"
    type: str = "flat"
    raw_or_label: str = "raw"
    raw_or_label_headers: str = "raw"
    export_checkbox_label: str = "false"
    export_survey_fields: str = "false"
    export_data_access_groups: str = "false"
    
    @classmethod
    def from_env(cls, project_id: Optional[str] = None) -> "REDCapConfig":
        """Create REDCap config from environment variables."""
        api_url = os.getenv("REDCAP_API_URL")
        api_token = os.getenv("REDCAP_API_TOKEN")
        
        if not api_url:
            raise ValueError("REDCAP_API_URL environment variable is required")
        if not api_token:
            raise ValueError("REDCAP_API_TOKEN environment variable is required")
        
        return cls(
            api_url=api_url,
            api_token=api_token,
            project_id=project_id or os.getenv("REDCAP_PROJECT_ID"),
            timeout=int(os.getenv("REDCAP_TIMEOUT", "30")),
            max_retries=int(os.getenv("REDCAP_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("REDCAP_RETRY_DELAY", "1.0"))
        )
    
    def get_export_payload(self, **kwargs) -> dict:
        """Get base payload for REDCap export requests."""
        payload = {
            'token': self.api_token,
            'content': 'record',
            'action': 'export',
            'format': self.format,
            'type': self.type,
            'rawOrLabel': self.raw_or_label,
            'rawOrLabelHeaders': self.raw_or_label_headers,
            'exportCheckboxLabel': self.export_checkbox_label,
            'exportSurveyFields': self.export_survey_fields,
            'exportDataAccessGroups': self.export_data_access_groups,
            'returnFormat': 'json'
        }
        
        # Add any additional parameters
        payload.update(kwargs)
        return payload
    
    def get_import_payload(self, data: str, **kwargs) -> dict:
        """Get base payload for REDCap import requests."""
        payload = {
            'token': self.api_token,
            'content': 'record',
            'action': 'import',
            'format': self.format,
            'type': self.type,
            'overwriteBehavior': 'overwrite',
            'forceAutoNumber': 'false',
            'data': data,
            'returnContent': 'count',
            'returnFormat': 'json'
        }
        
        # Add any additional parameters
        payload.update(kwargs)
        return payload


# Legacy support for existing code
def get_redcap_config() -> REDCapConfig:
    """Get REDCap configuration. For backwards compatibility."""
    return REDCapConfig.from_env()


# Export commonly used variables for backwards compatibility
try:
    _config = REDCapConfig.from_env()
    adrc_api_key = _config.api_token
    adrc_redcap_url = _config.api_url
    
    # Default UDS events - these should be configured based on your specific project
    uds_events = [
        "baseline_arm_1",
        "followup_1_arm_1", 
        "followup_2_arm_1",
        "followup_3_arm_1"
    ]
    
except ValueError:
    # If environment variables are not set, set to None to prevent import errors
    adrc_api_key = None
    adrc_redcap_url = None
    uds_events = []
