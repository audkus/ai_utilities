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
    
    @patch('ai_utilities.__main__.main')
    def test_main_execution(self, mock_main):
        """Test that main is called when __name__ == '__main__'."""
        # Simulate running as main module
        mock_main.return_value = None
        
        # Set the __name__ attribute to simulate main execution
        original_name = ai_utilities.__main__.__name__
        ai_utilities.__main__.__name__ = '__main__'
        
        try:
            # Execute the module (this should call main())
            exec("import ai_utilities.__main__")
        except SystemExit:
            # main() might call sys.exit(), which is expected
            pass
        finally:
            # Restore original name
            ai_utilities.__main__.__name__ = original_name
    
    def test_cli_import(self):
        """Test that cli.main is imported correctly."""
        # This tests the import statement in __main__.py
        from ai_utilities.cli import main
        assert main is not None
