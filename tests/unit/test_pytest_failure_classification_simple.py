"""Tests for pytest failure classification plugin."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest


def test_plugin_registration():
    """Test that the plugin can be registered without errors."""
    from ai_utilities.testing.pytest_failure_classification import FailureClassificationPlugin
    
    plugin = FailureClassificationPlugin()
    assert plugin.json_enabled is False  # Default when env var not set
    assert plugin.blocked_nodeids == []
    assert plugin.real_nodeids == []
    assert plugin.teardown_nodeids == []


def test_plugin_json_enabled():
    """Test plugin behavior when JSON output is enabled."""
    import os
    
    # Set env var for this test
    original_env = os.environ.get("AIU_PYTEST_FAILURE_JSON")
    os.environ["AIU_PYTEST_FAILURE_JSON"] = "1"
    
    try:
        from ai_utilities.testing.pytest_failure_classification import FailureClassificationPlugin
        
        plugin = FailureClassificationPlugin()
        assert plugin.json_enabled is True
        assert plugin.json_path == Path(".pytest_artifacts/failure_classification.json")
    finally:
        # Restore original env var
        if original_env is None:
            os.environ.pop("AIU_PYTEST_FAILURE_JSON", None)
        else:
            os.environ["AIU_PYTEST_FAILURE_JSON"] = original_env


def test_plugin_json_writing():
    """Test that plugin can write JSON file."""
    import os
    
    # Set env var for this test
    original_env = os.environ.get("AIU_PYTEST_FAILURE_JSON")
    os.environ["AIU_PYTEST_FAILURE_JSON"] = "1"
    
    try:
        from ai_utilities.testing.pytest_failure_classification import FailureClassificationPlugin
        
        plugin = FailureClassificationPlugin()
        
        # Use temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin.json_path = Path(tmpdir) / "test_classification.json"
            
            # Add some test failures
            plugin.blocked_nodeids = ["test_file.py::test_setup"]
            plugin.real_nodeids = ["test_file.py::test_assertion"]
            plugin.teardown_nodeids = ["test_file.py::test_cleanup"]
            plugin.pytest_exitstatus = 1
            
            # Write JSON file
            plugin._write_json_file()
            
            # Verify file exists and has correct content
            assert plugin.json_path.exists()
            
            with open(plugin.json_path) as f:
                data = json.load(f)
            
            assert data["blocked_count"] == 1
            assert data["real_count"] == 1
            assert data["teardown_count"] == 1
            assert data["blocked_nodeids"] == ["test_file.py::test_setup"]
            assert data["real_nodeids"] == ["test_file.py::test_assertion"]
            assert data["teardown_nodeids"] == ["test_file.py::test_cleanup"]
            assert "created_utc" in data
            assert data["pytest_exitstatus"] == 1
            
    finally:
        # Restore original env var
        if original_env is None:
            os.environ.pop("AIU_PYTEST_FAILURE_JSON", None)
        else:
            os.environ["AIU_PYTEST_FAILURE_JSON"] = original_env


def test_plugin_json_directory_creation():
    """Test that plugin creates directory for JSON file."""
    import os
    
    # Set env var for this test
    original_env = os.environ.get("AIU_PYTEST_FAILURE_JSON")
    os.environ["AIU_PYTEST_FAILURE_JSON"] = "1"
    
    try:
        from ai_utilities.testing.pytest_failure_classification import FailureClassificationPlugin
        
        plugin = FailureClassificationPlugin()
        
        # Use temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin.json_path = Path(tmpdir) / ".pytest_artifacts" / "test_classification.json"
            
            # Ensure directory doesn't exist initially
            assert not plugin.json_path.parent.exists()
            
            # Write JSON file (should create directory)
            plugin._write_json_file()
            
            # Verify directory was created and file exists
            assert plugin.json_path.parent.exists()
            assert plugin.json_path.exists()
            
    finally:
        # Restore original env var
        if original_env is None:
            os.environ.pop("AIU_PYTEST_FAILURE_JSON", None)
        else:
            os.environ["AIU_PYTEST_FAILURE_JSON"] = original_env


def test_plugin_no_json_when_disabled():
    """Test that plugin doesn't write JSON when disabled."""
    from ai_utilities.testing.pytest_failure_classification import FailureClassificationPlugin
    
    plugin = FailureClassificationPlugin()
    
    # Use temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin.json_path = Path(tmpdir) / "test_classification.json"
        
        # Add some test failures
        plugin.blocked_nodeids = ["test_file.py::test_setup"]
        
        # Try to write JSON file (should not write when disabled)
        plugin._write_json_file()
        
        # Verify file was NOT created
        assert not plugin.json_path.exists()


def test_plugin_handles_json_write_errors():
    """Test that plugin handles JSON write errors gracefully."""
    import os
    
    # Set env var for this test
    original_env = os.environ.get("AIU_PYTEST_FAILURE_JSON")
    os.environ["AIU_PYTEST_FAILURE_JSON"] = "1"
    
    try:
        from ai_utilities.testing.pytest_failure_classification import FailureClassificationPlugin
        
        plugin = FailureClassificationPlugin()
        
        # Set JSON path to a directory (should cause write error)
        plugin.json_path = Path("/")  # Root directory (unwritable)
        
        # This should not raise an exception
        plugin._write_json_file()  # Should fail silently
        
    finally:
        # Restore original env var
        if original_env is None:
            os.environ.pop("AIU_PYTEST_FAILURE_JSON", None)
        else:
            os.environ["AIU_PYTEST_FAILURE_JSON"] = original_env


def test_conftest_plugin_registration():
    """Test that conftest.py registers the plugin correctly."""
    # Import conftest and check that it has the pytest_configure function
    from tests import conftest
    
    assert hasattr(conftest, "pytest_configure")
    
    # Check that pytest_configure tries to import and register the plugin
    import inspect
    source = inspect.getsource(conftest.pytest_configure)
    
    assert "FailureClassificationPlugin" in source
    assert "failure_classification" in source
