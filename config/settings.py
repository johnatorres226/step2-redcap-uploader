"""Application settings and configuration."""

import os
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class Settings:
    """Main application settings."""
    
    # File monitoring
    CHECK_FILE_CHANGES: bool = True
    FILE_HASH_ALGORITHM: str = "sha256"
    
    # Data processing
    BATCH_SIZE: int = 100
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0  # seconds
    
    # Validation
    VALIDATE_DATA: bool = True
    STRICT_VALIDATION: bool = False
    
    # Logging
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_TO_FILE: bool = True
    LOG_TO_CONSOLE: bool = True
    
    # Directories
    BASE_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    DATA_DIR: Path = field(init=False)
    LOGS_DIR: Path = field(init=False)
    BACKUPS_DIR: Path = field(init=False)
    OUTPUT_DIR: Path = field(init=False)
    
    # Upload paths
    UPLOAD_READY_PATH: str = field(default_factory=lambda: os.getenv("UPLOAD_READY_PATH", "./data"))
    BACKUP_LOG_PATH: str = field(default_factory=lambda: os.getenv("BACKUP_LOG_PATH", "./backups"))
    
    # File tracking
    LAST_PROCESSED_FILE: str = ".last_processed"
    FILE_TRACKING_DB: str = "file_tracking.json"
    
    # REDCap specific
    DEFAULT_EVENTS: List[str] = field(default_factory=list)
    DEFAULT_FORMS: List[str] = field(default_factory=list)
    
    # Safety features
    DRY_RUN_DEFAULT: bool = False
    BACKUP_BEFORE_UPLOAD: bool = True
    CONFIRM_UPLOADS: bool = True
    
    def __post_init__(self):
        """Initialize computed fields."""
        self.DATA_DIR = self.BASE_DIR / "data"
        self.LOGS_DIR = self.BASE_DIR / "logs"
        self.BACKUPS_DIR = self.BASE_DIR / "backups"
        self.OUTPUT_DIR = self.BASE_DIR / "output"
        
        # Create directories if they don't exist
        for directory in [self.DATA_DIR, self.LOGS_DIR, self.BACKUPS_DIR, self.OUTPUT_DIR]:
            directory.mkdir(exist_ok=True)
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings instance from environment variables."""
        return cls(
            CHECK_FILE_CHANGES=os.getenv("CHECK_FILE_CHANGES", "true").lower() == "true",
            BATCH_SIZE=int(os.getenv("BATCH_SIZE", "100")),
            MAX_RETRIES=int(os.getenv("MAX_RETRIES", "3")),
            VALIDATE_DATA=os.getenv("VALIDATE_DATA", "true").lower() == "true",
            DRY_RUN_DEFAULT=os.getenv("DRY_RUN_DEFAULT", "false").lower() == "true",
        )
