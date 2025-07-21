"""Data processing and validation functionality."""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class DataProcessor:
    """Process and validate data for REDCap upload."""
    
    def __init__(self, strict_validation: bool = False):
        self.strict_validation = strict_validation
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
    
    def load_file(self, file_path: Path) -> pd.DataFrame:
        """Load data from Excel or CSV file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            # Determine file type and load accordingly
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                df = self._load_excel(file_path)
            elif file_path.suffix.lower() == '.csv':
                df = self._load_csv(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")
            
            logger.info(f"Loaded {len(df)} rows from {file_path}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
            raise
    
    def _load_excel(self, file_path: Path) -> pd.DataFrame:
        """Load Excel file with error handling."""
        try:
            # Try to load the first sheet
            df = pd.read_excel(file_path, sheet_name=0)
            logger.debug(f"Loaded Excel file with {len(df)} rows and {len(df.columns)} columns")
            return df
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            raise
    
    def _load_csv(self, file_path: Path) -> pd.DataFrame:
        """Load CSV file with error handling."""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    logger.debug(f"Loaded CSV file with encoding {encoding}: {len(df)} rows, {len(df.columns)} columns")
                    return df
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, raise error
            raise ValueError(f"Could not decode CSV file with any of these encodings: {encodings}")
            
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise
    
    def validate_required_columns(self, df: pd.DataFrame, required_columns: List[str]) -> bool:
        """Validate that required columns are present."""
        missing_columns = set(required_columns) - set(df.columns)
        
        if missing_columns:
            error_msg = f"Missing required columns: {missing_columns}"
            self.validation_errors.append(error_msg)
            logger.error(error_msg)
            return False
        
        logger.info("All required columns present")
        return True
    
    def validate_data_types(self, df: pd.DataFrame, column_types: Dict[str, str]) -> bool:
        """Validate data types for specified columns."""
        valid = True
        
        for column, expected_type in column_types.items():
            if column not in df.columns:
                continue
            
            try:
                if expected_type.lower() == 'numeric':
                    # Check if column can be converted to numeric
                    pd.to_numeric(df[column], errors='coerce')
                elif expected_type.lower() == 'date':
                    # Check if column can be converted to datetime
                    pd.to_datetime(df[column], errors='coerce')
                elif expected_type.lower() == 'string':
                    # Ensure column is string type
                    df[column].astype(str)
                
                logger.debug(f"Column '{column}' validated as {expected_type}")
                
            except Exception as e:
                error_msg = f"Column '{column}' failed {expected_type} validation: {e}"
                self.validation_errors.append(error_msg)
                logger.error(error_msg)
                valid = False
        
        return valid
    
    def validate_unique_keys(self, df: pd.DataFrame, key_columns: List[str]) -> bool:
        """Validate that key columns form unique combinations."""
        if not all(col in df.columns for col in key_columns):
            missing = [col for col in key_columns if col not in df.columns]
            error_msg = f"Key columns missing: {missing}"
            self.validation_errors.append(error_msg)
            logger.error(error_msg)
            return False
        
        # Check for duplicates
        duplicate_mask = df.duplicated(subset=key_columns, keep=False)
        duplicates = df[duplicate_mask]
        
        if not duplicates.empty:
            error_msg = f"Found {len(duplicates)} duplicate key combinations"
            self.validation_errors.append(error_msg)
            logger.error(error_msg)
            
            # Log some examples
            for i, (idx, row) in enumerate(duplicates.head().iterrows()):
                key_values = {col: row[col] for col in key_columns}
                logger.error(f"Duplicate {i+1}: {key_values}")
            
            return False
        
        logger.info(f"All {len(df)} rows have unique key combinations")
        return True
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize data."""
        df_cleaned = df.copy()
        
        # Remove completely empty rows
        initial_rows = len(df_cleaned)
        df_cleaned = df_cleaned.dropna(how='all')
        removed_rows = initial_rows - len(df_cleaned)
        
        if removed_rows > 0:
            logger.info(f"Removed {removed_rows} completely empty rows")
        
        # Standardize column names (strip whitespace, lowercase)
        df_cleaned.columns = [col.strip() for col in df_cleaned.columns]
        
        # Clean string columns (strip whitespace)
        string_columns = df_cleaned.select_dtypes(include=['object']).columns
        for col in string_columns:
            df_cleaned[col] = df_cleaned[col].astype(str).str.strip()
            # Replace 'nan' strings with actual NaN
            df_cleaned[col] = df_cleaned[col].replace(['nan', 'NaN', 'NULL', ''], np.nan)
        
        logger.info(f"Data cleaning completed: {len(df_cleaned)} rows remaining")
        return df_cleaned
    
    def standardize_redcap_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize REDCap-specific fields."""
        df_std = df.copy()
        
        # Ensure required REDCap fields exist
        redcap_fields = {
            'redcap_event_name': '',
            'redcap_repeat_instrument': '',
            'redcap_repeat_instance': ''
        }
        
        for field, default_value in redcap_fields.items():
            if field not in df_std.columns:
                df_std[field] = default_value
                logger.info(f"Added missing REDCap field: {field}")
        
        # Clean up redcap_repeat_instance (should be numeric or empty)
        if 'redcap_repeat_instance' in df_std.columns:
            df_std['redcap_repeat_instance'] = pd.to_numeric(
                df_std['redcap_repeat_instance'], 
                errors='coerce'
            ).fillna('')
        
        return df_std
    
    def filter_by_events(self, df: pd.DataFrame, events: List[str]) -> pd.DataFrame:
        """Filter data by REDCap events."""
        if not events or 'redcap_event_name' not in df.columns:
            return df
        
        initial_rows = len(df)
        df_filtered = df[df['redcap_event_name'].isin(events)]
        
        logger.info(f"Filtered by events {events}: {len(df_filtered)}/{initial_rows} rows retained")
        return df_filtered
    
    def validate_against_metadata(
        self, 
        df: pd.DataFrame, 
        metadata: List[Dict[str, Any]]
    ) -> bool:
        """Validate data against REDCap metadata."""
        if not metadata:
            logger.warning("No metadata provided for validation")
            return True
        
        # Create metadata lookup
        metadata_dict = {item['field_name']: item for item in metadata}
        valid = True
        
        for column in df.columns:
            if column in metadata_dict:
                field_info = metadata_dict[column]
                field_type = field_info.get('field_type', '')
                validation = field_info.get('text_validation_type_or_show_slider_number', '')
                
                # Validate based on field type
                if field_type == 'text' and validation:
                    valid &= self._validate_text_field(df, column, validation)
                elif field_type in ['radio', 'dropdown']:
                    valid &= self._validate_choice_field(df, column, field_info)
                elif field_type == 'yesno':
                    valid &= self._validate_yesno_field(df, column)
                elif field_type == 'checkbox':
                    valid &= self._validate_checkbox_field(df, column, field_info)
        
        return valid
    
    def _validate_text_field(self, df: pd.DataFrame, column: str, validation: str) -> bool:
        """Validate text field based on validation type."""
        valid = True
        
        if validation in ['integer', 'number']:
            non_numeric = df[df[column].notna() & pd.to_numeric(df[column], errors='coerce').isna()]
            if not non_numeric.empty:
                error_msg = f"Column '{column}' contains non-numeric values: {len(non_numeric)} rows"
                self.validation_errors.append(error_msg)
                valid = False
        
        elif validation == 'date_ymd':
            non_dates = df[df[column].notna() & pd.to_datetime(df[column], errors='coerce').isna()]
            if not non_dates.empty:
                error_msg = f"Column '{column}' contains invalid dates: {len(non_dates)} rows"
                self.validation_errors.append(error_msg)
                valid = False
        
        return valid
    
    def _validate_choice_field(self, df: pd.DataFrame, column: str, field_info: Dict) -> bool:
        """Validate radio/dropdown field choices."""
        choices_str = field_info.get('select_choices_or_calculations', '')
        if not choices_str:
            return True
        
        # Parse choices
        valid_choices = set()
        for choice in choices_str.split('|'):
            if ',' in choice:
                choice_value = choice.split(',')[0].strip()
                valid_choices.add(choice_value)
        
        if valid_choices:
            invalid_values = df[
                df[column].notna() & 
                ~df[column].astype(str).isin(valid_choices)
            ]
            
            if not invalid_values.empty:
                error_msg = f"Column '{column}' contains invalid choices: {len(invalid_values)} rows"
                self.validation_errors.append(error_msg)
                return False
        
        return True
    
    def _validate_yesno_field(self, df: pd.DataFrame, column: str) -> bool:
        """Validate yes/no field values."""
        valid_values = {'0', '1', 0, 1, 'yes', 'no', 'Yes', 'No'}
        invalid_values = df[
            df[column].notna() & 
            ~df[column].isin(valid_values)
        ]
        
        if not invalid_values.empty:
            error_msg = f"Column '{column}' contains invalid yes/no values: {len(invalid_values)} rows"
            self.validation_errors.append(error_msg)
            return False
        
        return True
    
    def _validate_checkbox_field(self, df: pd.DataFrame, column: str, field_info: Dict) -> bool:
        """Validate checkbox field values."""
        # Checkbox fields should be 0, 1, or empty
        valid_values = {'0', '1', 0, 1, '', np.nan}
        invalid_values = df[
            ~df[column].isin(valid_values)
        ]
        
        if not invalid_values.empty:
            error_msg = f"Checkbox column '{column}' contains invalid values: {len(invalid_values)} rows"
            self.validation_errors.append(error_msg)
            return False
        
        return True
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation results."""
        return {
            'errors': self.validation_errors.copy(),
            'warnings': self.validation_warnings.copy(),
            'error_count': len(self.validation_errors),
            'warning_count': len(self.validation_warnings),
            'is_valid': len(self.validation_errors) == 0
        }
    
    def clear_validation_results(self) -> None:
        """Clear validation results."""
        self.validation_errors.clear()
        self.validation_warnings.clear()
