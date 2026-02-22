"""Tests for the CI failure classification script."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.ci.check_failure_classification import (
    get_blocked_count,
    get_blocked_nodeids,
    main,
    print_blocked_nodeids,
    read_failure_classification,
)


class TestReadFailureClassification:
    """Test reading and parsing failure classification files."""

    def test_missing_file_exits_with_code_1(self, capsys):
        """Test that missing file causes exit with code 1."""
        with pytest.raises(SystemExit) as exc_info:
            read_failure_classification(Path("nonexistent.json"))
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "❌ CI FAILED: Failure classification JSON not found" in captured.out

    def test_invalid_json_exits_with_code_1(self, capsys, tmp_path):
        """Test that invalid JSON causes exit with code 1."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json")
        
        with pytest.raises(SystemExit) as exc_info:
            read_failure_classification(invalid_file)
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "❌ CI FAILED: Failure classification JSON is invalid" in captured.out

    def test_valid_json_returns_data(self, tmp_path):
        """Test that valid JSON returns parsed data."""
        valid_data = {"blocked_count": 2, "blocked_nodeids": ["test1", "test2"]}
        valid_file = tmp_path / "valid.json"
        valid_file.write_text(json.dumps(valid_data))
        
        result = read_failure_classification(valid_file)
        assert result == valid_data


class TestGetBlockedCount:
    """Test extraction of blocked count from data."""

    def test_blocked_count_present(self):
        """Test extracting blocked count when present."""
        data = {"blocked_count": 5}
        assert get_blocked_count(data) == 5

    def test_blocked_count_missing(self):
        """Test extracting blocked count when missing."""
        data = {}
        assert get_blocked_count(data) == 0

    def test_blocked_count_string(self):
        """Test converting string blocked count to int."""
        data = {"blocked_count": "3"}
        assert get_blocked_count(data) == 3


class TestGetBlockedNodeids:
    """Test extraction of blocked node IDs from data."""

    def test_blocked_nodeids_present(self):
        """Test extracting blocked node IDs when present."""
        data = {"blocked_nodeids": ["test1.py::test_func", "test2.py::test_func"]}
        assert get_blocked_nodeids(data) == ["test1.py::test_func", "test2.py::test_func"]

    def test_blocked_nodeids_missing(self):
        """Test extracting blocked node IDs when missing."""
        data = {}
        assert get_blocked_nodeids(data) == []


class TestPrintBlockedNodeids:
    """Test printing of blocked node IDs."""

    def test_print_empty_list(self, capsys):
        """Test printing empty node ID list."""
        print_blocked_nodeids([])
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_print_short_list(self, capsys):
        """Test printing node ID list shorter than max display."""
        nodeids = ["test1.py::test_func", "test2.py::test_func"]
        print_blocked_nodeids(nodeids)
        captured = capsys.readouterr()
        assert "Failure details:" in captured.out
        assert "  - test1.py::test_func" in captured.out
        assert "  - test2.py::test_func" in captured.out
        assert "... and" not in captured.out

    def test_print_long_list_truncates(self, capsys):
        """Test printing node ID list longer than max display gets truncated."""
        nodeids = [f"test{i}.py::test_func" for i in range(15)]
        print_blocked_nodeids(nodeids, max_display=10)
        captured = capsys.readouterr()
        assert "Failure details:" in captured.out
        assert "  - test0.py::test_func" in captured.out
        assert "  - test9.py::test_func" in captured.out
        assert "  ... and 5 more" in captured.out
        assert "test10.py::test_func" not in captured.out


class TestMain:
    """Test main script behavior."""

    def test_missing_json_file_exits_with_code_1(self, capsys):
        """Test main function exits with code 1 when JSON file is missing."""
        with patch("scripts.ci.check_failure_classification.Path") as mock_path:
            mock_path.return_value.exists.return_value = False
            
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "❌ CI FAILED: Failure classification JSON not found" in captured.out

    def test_blocked_failures_exits_with_code_1(self, capsys, tmp_path):
        """Test main function exits with code 1 when blocked failures exist."""
        # Create test data with blocked failures
        test_data = {
            "blocked_count": 2,
            "blocked_nodeids": ["test1.py::test_func", "test2.py::test_func"]
        }
        
        json_file = tmp_path / ".pytest_artifacts" / "failure_classification.json"
        json_file.parent.mkdir(exist_ok=True)
        json_file.write_text(json.dumps(test_data))
        
        with patch("scripts.ci.check_failure_classification.Path") as mock_path:
            mock_path.return_value = json_file
            
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "❌ CI FAILED: 2 blocked test(s) detected" in captured.out
            assert "Blocked tests indicate collection or setup failures" in captured.out
            assert "  - test1.py::test_func" in captured.out
            assert "  - test2.py::test_func" in captured.out

    def test_no_blocked_failures_exits_with_code_0(self, capsys, tmp_path):
        """Test main function exits with code 0 when no blocked failures exist."""
        # Create test data with no blocked failures
        test_data = {"blocked_count": 0, "blocked_nodeids": []}
        
        json_file = tmp_path / ".pytest_artifacts" / "failure_classification.json"
        json_file.parent.mkdir(exist_ok=True)
        json_file.write_text(json.dumps(test_data))
        
        with patch("scripts.ci.check_failure_classification.Path") as mock_path:
            mock_path.return_value = json_file
            
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert "✅ No blocked test failures detected" in captured.out

    def test_missing_blocked_count_defaults_to_zero(self, capsys, tmp_path):
        """Test main function treats missing blocked_count as zero."""
        # Create test data without blocked_count
        test_data = {"some_other_field": "value"}
        
        json_file = tmp_path / ".pytest_artifacts" / "failure_classification.json"
        json_file.parent.mkdir(exist_ok=True)
        json_file.write_text(json.dumps(test_data))
        
        with patch("scripts.ci.check_failure_classification.Path") as mock_path:
            mock_path.return_value = json_file
            
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert "✅ No blocked test failures detected" in captured.out
