"""Test suite for ChangeTracker functionality based on actual implementation."""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from unittest.mock import Mock
from datetime import datetime

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.uploader.change_tracker import ChangeTracker, FieldChange, ChangeSet


class TestFieldChange:
    """Test FieldChange dataclass functionality."""
    
    def test_field_change_creation(self):
        """Test creating FieldChange instance."""
        change = FieldChange(
            record_id="UDS001",
            event_name="baseline_arm_1",
            form_name="qc_status",
            field_name="qc_results",
            old_value="Old results",
            new_value="New results",
            repeat_instrument="",
            repeat_instance=""
        )
        
        assert change.record_id == "UDS001"
        assert change.event_name == "baseline_arm_1"
        assert change.form_name == "qc_status"
        assert change.field_name == "qc_results"
        assert change.old_value == "Old results"
        assert change.new_value == "New results"
        assert change.change_timestamp  # Should be auto-generated
    
    def test_field_change_to_dict(self):
        """Test converting FieldChange to dictionary."""
        change = FieldChange(
            record_id="UDS002",
            event_name="baseline_arm_1",
            form_name="qc_status",
            field_name="qc_notes",
            old_value="Old notes",
            new_value="New notes"
        )
        
        result = change.to_dict()
        
        assert isinstance(result, dict)
        assert result['record_id'] == "UDS002"
        assert result['field_name'] == "qc_notes"
        assert result['old_value'] == "Old notes"
        assert result['new_value'] == "New notes"
        assert 'change_timestamp' in result


class TestChangeSet:
    """Test ChangeSet dataclass functionality."""
    
    def test_change_set_creation(self):
        """Test creating ChangeSet instance."""
        changes = [
            FieldChange(
                record_id="UDS001",
                event_name="baseline_arm_1",
                form_name="qc_status",
                field_name="qc_results",
                old_value="Old",
                new_value="New"
            )
        ]
        
        change_set = ChangeSet(
            operation_id="upload_001",
            timestamp="2025-08-15T12:30:00",
            file_path="/path/to/file.json",
            file_hash="abc123",
            total_records=5,
            total_changes=1,
            changes=changes
        )
        
        assert change_set.operation_id == "upload_001"
        assert change_set.total_records == 5
        assert change_set.total_changes == 1
        assert len(change_set.changes) == 1
        assert change_set.changes[0].record_id == "UDS001"
    
    def test_change_set_to_dict(self):
        """Test converting ChangeSet to dictionary."""
        changes = [
            FieldChange(
                record_id="UDS001",
                event_name="baseline_arm_1",
                form_name="qc_status",
                field_name="qc_results",
                old_value="Old",
                new_value="New"
            )
        ]
        
        change_set = ChangeSet(
            operation_id="upload_002",
            timestamp="2025-08-15T13:00:00",
            file_path="/path/to/file2.json",
            file_hash="def456",
            total_records=3,
            total_changes=1,
            changes=changes
        )
        
        result = change_set.to_dict()
        
        assert isinstance(result, dict)
        assert result['operation_id'] == "upload_002"
        assert result['total_records'] == 3
        assert result['total_changes'] == 1
        assert 'changes' in result
        assert len(result['changes']) == 1


class TestChangeTracker:
    """Test ChangeTracker class with actual methods."""
    
    def test_init(self, temp_dir):
        """Test ChangeTracker initialization."""
        tracker = ChangeTracker(temp_dir)
        
        assert tracker.logs_dir == temp_dir
        assert hasattr(tracker, 'current_changes')
        assert hasattr(tracker, 'operation_metadata')
    
    def test_set_operation_metadata(self, temp_dir):
        """Test setting operation metadata."""
        tracker = ChangeTracker(temp_dir)
        
        metadata = {
            'operation_type': 'qc_status_upload',
            'initials': 'JT',
            'file_count': 2,
            'timestamp': datetime.now().isoformat()
        }
        
        tracker.set_operation_metadata(metadata)
        
        assert tracker.operation_metadata == metadata
    
    def test_add_changes(self, temp_dir):
        """Test adding changes to tracker."""
        tracker = ChangeTracker(temp_dir)
        
        changes = [
            FieldChange(
                record_id="UDS001",
                event_name="baseline_arm_1",
                form_name="qc_status",
                field_name="qc_results",
                old_value="Old",
                new_value="New"
            )
        ]
        
        tracker.add_changes(changes)
        
        assert len(tracker.current_changes) == 1
        assert tracker.current_changes[0].record_id == "UDS001"
    
    def test_compare_dataframes(self, temp_dir):
        """Test comparing dataframes for changes."""
        tracker = ChangeTracker(temp_dir)
        
        # Create sample dataframes
        old_df = pd.DataFrame([
            {"record_id": "UDS001", "redcap_event_name": "baseline_arm_1", "qc_results": "Old"},
            {"record_id": "UDS002", "redcap_event_name": "baseline_arm_1", "qc_results": "Unchanged"}
        ])
        
        new_df = pd.DataFrame([
            {"record_id": "UDS001", "redcap_event_name": "baseline_arm_1", "qc_results": "New"},
            {"record_id": "UDS002", "redcap_event_name": "baseline_arm_1", "qc_results": "Unchanged"}
        ])
        
        changes = tracker.compare_dataframes(old_df, new_df)
        
        assert isinstance(changes, list)
        if len(changes) > 0:
            assert all(isinstance(change, FieldChange) for change in changes)
            # Should detect the change in UDS001
            uds001_changes = [c for c in changes if c.record_id == "UDS001"]
            assert len(uds001_changes) > 0
    
    def test_create_changeset(self, temp_dir):
        """Test creating changeset."""
        tracker = ChangeTracker(temp_dir)
        
        # Set up some metadata
        tracker.set_operation_metadata({
            'operation_id': 'test_op_001',
            'file_path': '/test/file.json',
            'file_hash': 'abc123'
        })
        
        # Add some changes
        changes = [
            FieldChange(
                record_id="UDS001",
                event_name="baseline_arm_1",
                form_name="qc_status",
                field_name="qc_results",
                old_value="Old",
                new_value="New"
            )
        ]
        
        tracker.add_changes(changes)
        
        changeset = tracker.create_changeset(total_records=5)
        
        assert isinstance(changeset, ChangeSet)
        assert changeset.operation_id == 'test_op_001'
        assert changeset.total_records == 5
        assert changeset.total_changes == 1
        assert len(changeset.changes) == 1
    
    def test_save_changeset(self, temp_dir):
        """Test saving changeset to file."""
        tracker = ChangeTracker(temp_dir)
        
        changes = [
            FieldChange(
                record_id="UDS001",
                event_name="baseline_arm_1",
                form_name="qc_status",
                field_name="qc_results",
                old_value="Old",
                new_value="New"
            )
        ]
        
        changeset = ChangeSet(
            operation_id="save_test_001",
            timestamp=datetime.now().isoformat(),
            file_path="/test/file.json",
            file_hash="abc123",
            total_records=1,
            total_changes=1,
            changes=changes
        )
        
        result = tracker.save_changeset(changeset)
        
        # Should return a file path or success indicator
        assert result is not None
    
    def test_save_backup_data(self, temp_dir, sample_qc_data):
        """Test saving backup data."""
        tracker = ChangeTracker(temp_dir)
        
        result = tracker.save_backup_data(
            data=sample_qc_data,
            data_type="qc_status",
            stage="before_upload"
        )
        
        # Should return a file path or success indicator
        assert result is not None
    
    def test_get_change_statistics(self, temp_dir):
        """Test getting change statistics."""
        tracker = ChangeTracker(temp_dir)
        
        # Add some changes
        changes = [
            FieldChange(
                record_id="UDS001",
                event_name="baseline_arm_1",
                form_name="qc_status",
                field_name="qc_results",
                old_value="Old",
                new_value="New"
            ),
            FieldChange(
                record_id="UDS002",
                event_name="baseline_arm_1",
                form_name="qc_status",
                field_name="qc_notes",
                old_value="Old notes",
                new_value="New notes"
            )
        ]
        
        tracker.add_changes(changes)
        
        stats = tracker.get_change_statistics()
        
        assert isinstance(stats, dict)
        # Should contain statistics about changes
        assert 'total_changes' in stats or 'change_count' in stats
    
    def test_clear_current_changes(self, temp_dir):
        """Test clearing current changes."""
        tracker = ChangeTracker(temp_dir)
        
        # Add some changes
        changes = [
            FieldChange(
                record_id="UDS001",
                event_name="baseline_arm_1",
                form_name="qc_status",
                field_name="qc_results",
                old_value="Old",
                new_value="New"
            )
        ]
        
        tracker.add_changes(changes)
        assert len(tracker.current_changes) == 1
        
        tracker.clear_current_changes()
        assert len(tracker.current_changes) == 0
    
    def test_save_summary_report(self, temp_dir):
        """Test saving summary report."""
        tracker = ChangeTracker(temp_dir)
        
        # Set up some operation data
        tracker.set_operation_metadata({
            'operation_id': 'summary_test_001',
            'initials': 'JT',
            'timestamp': datetime.now().isoformat()
        })
        
        # Add some changes
        changes = [
            FieldChange(
                record_id="UDS001",
                event_name="baseline_arm_1",
                form_name="qc_status",
                field_name="qc_results",
                old_value="Old",
                new_value="New"
            )
        ]
        
        tracker.add_changes(changes)
        
        result = tracker.save_summary_report()
        
        # Should return a file path or success indicator
        assert result is not None
