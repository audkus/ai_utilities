"""Tests for SSL backend compatibility checking."""

import ssl
import warnings
import pytest
from unittest.mock import patch, MagicMock

# Test importing the module to cover import lines
import ai_utilities.ssl_check

from ai_utilities.ssl_check import (
    get_ssl_backend_info,
    check_ssl_backend,
    emit_ssl_compatibility_warning,
    require_ssl_backend,
    SSLBackendCompatibilityWarning,
    _warning_emitted
)


class TestSSLBackendCheck:
    """Test SSL backend checking functionality."""

    def test_module_imports_and_warning_class(self) -> None:
        """Test that module imports and warning class work correctly."""
        # Test the warning class inheritance
        warning = SSLBackendCompatibilityWarning("Test warning")
        assert isinstance(warning, UserWarning)
        assert isinstance(warning, Warning)
        assert str(warning) == "Test warning"

    def test_module_level_flag_exists(self) -> None:
        """Test that the module-level warning flag exists."""
        # Access the module-level flag to ensure it's covered
        assert isinstance(_warning_emitted, bool)

    def test_get_ssl_backend_info(self):
        """Test SSL backend info retrieval."""
        info = get_ssl_backend_info()
        
        # Check required keys
        assert "version" in info
        assert "version_info" in info
        assert "is_libressl" in info
        assert "is_openssl" in info
        
        # Check data types
        assert isinstance(info["version"], str)
        assert isinstance(info["version_info"], tuple)
        assert isinstance(info["is_libressl"], bool)
        assert isinstance(info["is_openssl"], bool)
        
        # Check mutual exclusivity
        assert not (info["is_libressl"] and info["is_openssl"])

    def test_check_ssl_backend(self):
        """Test SSL backend check returns boolean."""
        result = check_ssl_backend()
        assert isinstance(result, bool)

    @patch('ai_utilities.ssl_check.get_ssl_backend_info')
    def test_emit_ssl_compatibility_warning_libressl(self, mock_info):
        """Test warning emission for LibreSSL."""
        mock_info.return_value = {
            "version": "LibreSSL 2.8.3",
            "version_info": (2, 8, 3),
            "is_libressl": True,
            "is_openssl": False,
        }
        
        # Reset the module-level warning flag
        import ai_utilities.ssl_check
        ai_utilities.ssl_check._warning_emitted = False
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            emit_ssl_compatibility_warning()
            
            assert len(w) == 1
            assert issubclass(w[0].category, SSLBackendCompatibilityWarning)
            assert "LibreSSL" in str(w[0].message)
            assert "ai_utilities" in str(w[0].message)
            assert "environment compatibility notice" in str(w[0].message)
            assert "Network functionality may be affected" in str(w[0].message)

    @patch('ai_utilities.ssl_check.get_ssl_backend_info')
    def test_emit_ssl_compatibility_warning_openssl(self, mock_info):
        """Test no warning for OpenSSL."""
        mock_info.return_value = {
            "version": "OpenSSL 1.1.1f",
            "version_info": (1, 1, 1, 15),
            "is_libressl": False,
            "is_openssl": True,
        }
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            emit_ssl_compatibility_warning()
            
            assert len(w) == 0

    def test_require_ssl_backend(self):
        """Test require_ssl_backend function."""
        # This should not raise an exception
        require_ssl_backend()

    def test_warning_can_be_filtered(self):
        """Test that warnings can be filtered by pytest."""
        # This test ensures the warning can be filtered with specific class
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SSLBackendCompatibilityWarning)
            # Should not emit any visible warnings
            require_ssl_backend()

    def test_warning_emitted_once_per_process(self):
        """Test that warning is only emitted once per process."""
        # Reset the module-level warning flag
        import ai_utilities.ssl_check
        ai_utilities.ssl_check._warning_emitted = False
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Call multiple times
            emit_ssl_compatibility_warning()
            emit_ssl_compatibility_warning()
            emit_ssl_compatibility_warning()
            
            # Should only have one warning
            assert len(w) == 1

    @patch('ssl.OPENSSL_VERSION', 'LibreSSL 2.8.3')
    def test_real_libressl_detection(self):
        """Test actual LibreSSL detection with mocked ssl module."""
        info = get_ssl_backend_info()
        assert info["is_libressl"] is True
        assert info["is_openssl"] is False
        assert "LibreSSL" in info["version"]

    @patch('ssl.OPENSSL_VERSION', 'OpenSSL 1.1.1f')
    def test_real_openssl_detection(self):
        """Test actual OpenSSL detection with mocked ssl module."""
        info = get_ssl_backend_info()
        assert info["is_openssl"] is True
        assert info["is_libressl"] is False
        assert "OpenSSL" in info["version"]

    def test_custom_warning_class_hierarchy(self):
        """Test that custom warning class is a UserWarning subclass."""
        assert issubclass(SSLBackendCompatibilityWarning, UserWarning)
        assert issubclass(SSLBackendCompatibilityWarning, Warning)
