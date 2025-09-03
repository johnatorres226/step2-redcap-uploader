"""Test suite for DataProcessor functionality."""

import sys
import json
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.uploader.data_processor import DataProcessor


class TestDataProcessor:
    """Test DataProcessor class functionality."""
    
    def test_init(self):
        """Test DataProcessor initialization."""
        processor = DataProcessor(strict_validation=True)
        
        assert processor.strict_validation is True
        assert isinstance(processor.validation_errors, list)
        assert isinstance(processor.validation_warnings, list)
        assert len(processor.validation_errors) == 0
        assert len(processor.validation_warnings) == 0
    
    def test_init_default_validation(self):
        """Test DataProcessor initialization with default validation."""
        processor = DataProcessor()
        
        assert processor.strict_validation is False
    
    def test_load_excel_file(self, temp_dir):
        """Test loading Excel file."""
        processor = DataProcessor()
        
        # Create sample Excel file
        sample_data = pd.DataFrame({
            'record_id': ['UDS001', 'UDS002', 'UDS003'],
            'ptid': ['UDS001', 'UDS002', 'UDS003'],
            'qc_status': [1, 2, 1],
            'qc_results': ['Pass', 'Fail', 'Pass']
        })
        
        excel_file = temp_dir / "test_data.xlsx"
        sample_data.to_excel(excel_file, index=False)
        
        df = processor.load_file(excel_file)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert 'record_id' in df.columns
        assert 'ptid' in df.columns
        assert df.iloc[0]['record_id'] == 'UDS001'
    
    def test_load_csv_file(self, temp_dir):
        """Test loading CSV file."""
        processor = DataProcessor()
        
        # Create sample CSV file
        csv_file = temp_dir / "test_data.csv"
        csv_content = """record_id,ptid,qc_status,qc_results
UDS001,UDS001,1,Pass
UDS002,UDS002,2,Fail
UDS003,UDS003,1,Pass"""
        
        with open(csv_file, 'w') as f:
            f.write(csv_content)
        
        df = processor.load_file(csv_file)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert 'record_id' in df.columns
        assert df.iloc[0]['record_id'] == 'UDS001'
    
    def test_load_file_not_found(self):
        """Test loading non-existent file."""
        processor = DataProcessor()
        
        try:
            processor.load_file(Path("nonexistent.xlsx"))
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass  # Expected
    
    def test_load_unsupported_file_type(self, temp_dir):
        """Test loading unsupported file type."""
        processor = DataProcessor()
        
        txt_file = temp_dir / "test_data.txt"
        with open(txt_file, 'w') as f:
            f.write("Some text content")
        
        try:
            processor.load_file(txt_file)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unsupported file type" in str(e)
    
    def test_validate_qc_status_data_valid(self):
        """Test validating valid QC status data."""
        processor = DataProcessor()
        
        valid_data = [
            {
                'record_id': 'UDS001',
                'redcap_event_name': 'baseline_arm_1',
                'ptid': 'UDS001',
                'qc_status': '1',
                'qc_last_run': '15AUG2025',
                'qc_results': 'All checks passed',
                'qc_run_by': 'JT'
            },
            {
                'record_id': 'UDS002',
                'redcap_event_name': 'baseline_arm_1',
                'ptid': 'UDS002',
                'qc_status': '2',
                'qc_last_run': '16AUG2025',
                'qc_results': 'Minor issues corrected',
                'qc_run_by': 'JT'
            }
        ]
        
        result = processor.validate_qc_status_data(valid_data)
        
        assert result['valid'] is True
        assert result['record_count'] == 2
        assert len(result['errors']) == 0
    
    def test_validate_qc_status_data_missing_required_fields(self):
        """Test validating QC data with missing required fields."""
        processor = DataProcessor(strict_validation=True)
        
        invalid_data = [
            {
                'record_id': 'UDS001',
                # Missing required fields
            }
        ]
        
        result = processor.validate_qc_status_data(invalid_data)
        
        assert result['valid'] is False
        assert len(result['errors']) > 0
        assert any('required field' in error.lower() for error in result['errors'])
    
    def test_validate_qc_status_data_invalid_date_format(self):
        """Test validating QC data with invalid date format."""
        processor = DataProcessor()
        
        invalid_data = [
            {
                'record_id': 'UDS001',
                'redcap_event_name': 'baseline_arm_1',
                'ptid': 'UDS001',
                'qc_status': '1',
                'qc_last_run': '2025-08-15',  # Wrong format, should be DDMMMYYYY
                'qc_results': 'All checks passed',
                'qc_run_by': 'JT'
            }
        ]
        
        result = processor.validate_qc_status_data(invalid_data)
        
        # Should still be valid in non-strict mode, but may have warnings
        assert result['valid'] is True or len(result['warnings']) > 0
    
    def test_validate_qc_status_data_empty_data(self):
        """Test validating empty data."""
        processor = DataProcessor()
        
        result = processor.validate_qc_status_data([])
        
        assert result['valid'] is False
        assert 'No data to validate' in result['errors'][0]
    
    def test_clean_and_normalize_data(self):
        """Test cleaning and normalizing data."""
        processor = DataProcessor()
        
        raw_data = [
            {
                'record_id': ' UDS001 ',  # Extra whitespace
                'ptid': 'UDS001',
                'qc_status': 1,  # Integer instead of string
                'qc_results': 'All checks passed',
                'empty_field': '',  # Empty field
                'null_field': None  # Null field
            },
            {
                'record_id': 'UDS002',
                'ptid': 'UDS002',
                'qc_status': '2',
                'qc_results': 'Minor issues'
            }
        ]
        
        cleaned_data = processor.clean_and_normalize_data(raw_data)
        
        assert len(cleaned_data) == 2
        assert cleaned_data[0]['record_id'] == 'UDS001'  # Whitespace removed
        assert cleaned_data[0]['qc_status'] == '1'  # Converted to string
        assert 'empty_field' not in cleaned_data[0] or cleaned_data[0]['empty_field'] == ''
    
    def test_convert_dataframe_to_redcap_format(self):
        """Test converting DataFrame to REDCap format."""
        processor = DataProcessor()
        
        df = pd.DataFrame({
            'record_id': ['UDS001', 'UDS002'],
            'ptid': ['UDS001', 'UDS002'],
            'qc_status': [1, 2],
            'qc_results': ['Pass', 'Fail']
        })
        
        redcap_data = processor.convert_dataframe_to_redcap_format(df)
        
        assert isinstance(redcap_data, list)
        assert len(redcap_data) == 2
        assert redcap_data[0]['record_id'] == 'UDS001'
        assert isinstance(redcap_data[0]['qc_status'], str)  # Should be converted to string
    
    def test_handle_special_characters(self):
        """Test handling special characters in data."""
        processor = DataProcessor()
        
        data_with_special_chars = [
            {
                'record_id': 'UDS001',
                'qc_results': 'Results with "quotes" and \n newlines',
                'qc_notes': 'Notes with & ampersand'
            }
        ]
        
        cleaned_data = processor.clean_and_normalize_data(data_with_special_chars)
        
        assert len(cleaned_data) == 1
        # Should handle special characters without breaking
        assert 'quotes' in cleaned_data[0]['qc_results']
    
    def test_validate_field_types(self):
        """Test field type validation."""
        processor = DataProcessor(strict_validation=True)
        
        data_with_wrong_types = [
            {
                'record_id': 123,  # Should be string
                'qc_status': 'invalid_status',  # Should be valid status code
                'qc_visit_date': 'not_a_date'  # Should be valid date
            }
        ]
        
        result = processor.validate_qc_status_data(data_with_wrong_types)
        
        # In strict mode, should catch type errors
        if processor.strict_validation:
            assert result['valid'] is False or len(result['warnings']) > 0
    
    def test_process_large_dataset(self):
        """Test processing large datasets."""
        processor = DataProcessor()
        
        # Create large dataset
        large_data = []
        for i in range(1000):
            large_data.append({
                'record_id': f'UDS{i:04d}',
                'ptid': f'UDS{i:04d}',
                'qc_status': str(i % 3 + 1),
                'qc_results': f'Results for record {i}',
                'qc_last_run': '15AUG2025',
                'qc_run_by': 'JT'
            })
        
        result = processor.validate_qc_status_data(large_data)
        
        assert result['valid'] is True
        assert result['record_count'] == 1000
    
    def test_handle_missing_optional_fields(self):
        """Test handling missing optional fields."""
        processor = DataProcessor()
        
        minimal_data = [
            {
                'record_id': 'UDS001',
                'ptid': 'UDS001',
                'qc_status': '1'
                # Missing optional fields like qc_notes, qc_results
            }
        ]
        
        result = processor.validate_qc_status_data(minimal_data)
        
        # Should be valid even with missing optional fields
        assert result['valid'] is True
    
    def test_error_accumulation(self):
        """Test that validation errors are properly accumulated."""
        processor = DataProcessor()
        
        # Clear any existing errors
        processor.validation_errors = []
        processor.validation_warnings = []
        
        # Add some errors
        processor.validation_errors.append("Test error 1")
        processor.validation_errors.append("Test error 2")
        processor.validation_warnings.append("Test warning 1")
        
        assert len(processor.validation_errors) == 2
        assert len(processor.validation_warnings) == 1
        assert "Test error 1" in processor.validation_errors
    
    def test_excel_file_with_multiple_sheets(self, temp_dir):
        """Test loading Excel file with multiple sheets."""
        processor = DataProcessor()
        
        # Create Excel file with multiple sheets
        excel_file = temp_dir / "multi_sheet.xlsx"
        
        with pd.ExcelWriter(excel_file) as writer:
            # Sheet 1
            df1 = pd.DataFrame({
                'record_id': ['UDS001', 'UDS002'],
                'data': ['A', 'B']
            })
            df1.to_excel(writer, sheet_name='Sheet1', index=False)
            
            # Sheet 2
            df2 = pd.DataFrame({
                'record_id': ['UDS003', 'UDS004'],
                'data': ['C', 'D']
            })
            df2.to_excel(writer, sheet_name='Sheet2', index=False)
        
        # Should load the first sheet by default
        df = processor.load_file(excel_file)
        
        assert len(df) == 2
        assert df.iloc[0]['record_id'] == 'UDS001'
    
    def test_csv_with_different_encodings(self, temp_dir):
        """Test loading CSV files with different encodings."""
        processor = DataProcessor()
        
        # Create CSV with UTF-8 encoding
        csv_file = temp_dir / "utf8_data.csv"
        csv_content = """record_id,ptid,notes
UDS001,UDS001,Special chars: éñüñ
UDS002,UDS002,More chars: ñüéî"""
        
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        df = processor.load_file(csv_file)
        
        assert len(df) == 2
        assert 'Special chars' in df.iloc[0]['notes']
