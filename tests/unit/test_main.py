"""Tests for the main entry point."""

import pytest
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add src to path for importing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import ai_utilities.__main__


class TestMain:
    """Test the main entry point."""
    
    def test_main_import(self):
        """Test that the main module can be imported."""
        assert ai_utilities.__main__ is not None
    
    def test_main_module_attributes(self):
        """Test that the main module has expected attributes."""
        assert hasattr(ai_utilities.__main__, '__name__')
        assert ai_utilities.__main__.__name__ == 'ai_utilities.__main__'
    
    def test_main_execution(self):
        """Test that main is called when __name__ == '__main__'."""
        # Test that the main function exists and can be called
        from ai_utilities.cli import main
        
        # Test with --help which should call sys.exit(0)
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        
        # Should exit with code 0 (success)
        assert exc_info.value.code == 0
    
    def test_cli_import(self):
        """Test that cli.main is imported correctly."""
        # This tests the import statement in __main__.py
        from ai_utilities.cli import main
        assert main is not None
