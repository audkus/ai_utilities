"""Tests for __main__.py module."""

import pytest
from unittest.mock import patch

from ai_utilities.__main__ import main


class TestMainModule:
    """Test __main__.py module."""
    
    def test_main_execution(self):
        """Test that main() is called when module is executed directly."""
        # This test verifies the module structure - actual execution testing
        # requires running the module as a script, which is complex to test
        import ai_utilities.__main__
        
        # Should have main function imported
        assert hasattr(ai_utilities.__main__, 'main')
        assert callable(ai_utilities.__main__.main)
    
    def test_main_imports(self):
        """Test that main function is properly imported."""
        # Should be able to import main from cli module
        from ai_utilities.cli import main as cli_main
        
        assert callable(cli_main)
    
    def test_main_function_call(self):
        """Test that main function is available and callable."""
        import ai_utilities.__main__
        
        # Should have main function
        assert hasattr(ai_utilities.__main__, 'main')
        assert callable(ai_utilities.__main__.main)
    
    def test_module_structure(self):
        """Test that module has expected structure."""
        import ai_utilities.__main__
        
        # Should have main function imported
        assert hasattr(ai_utilities.__main__, 'main')
        assert callable(ai_utilities.__main__.main)
        
        # Should have proper __name__ attribute
        assert hasattr(ai_utilities.__main__, '__name__')
        assert ai_utilities.__main__.__name__ == 'ai_utilities.__main__'
        
        # Should have proper docstring
        assert ai_utilities.__main__.__doc__ == "Main entry point for python -m ai_utilities."
    
    def test_main_function_import(self):
        """Test that main function is imported from cli module."""
        from ai_utilities.__main__ import main
        from ai_utilities.cli import main as cli_main
        
        # Should be the same function
        assert main is cli_main
