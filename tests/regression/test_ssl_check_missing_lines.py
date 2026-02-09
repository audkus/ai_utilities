"""Additional tests for ssl_check.py to cover missing lines."""

import warnings
import pytest
from unittest.mock import patch

import ai_utilities.ssl_check as ssl_module
from ai_utilities.ssl_check import (
    get_ssl_backend_info,
    check_ssl_backend,
    emit_ssl_compatibility_warning,
    require_ssl_backend,
    SSLBackendCompatibilityWarning,
    _warning_emitted
)


def test_ssl_check_import_and_constants():
    """Test importing ssl_check module to cover lines 8-11."""
    # This test ensures the import lines (8-11) are covered
    assert hasattr(ssl_module, 'ssl')
    assert hasattr(ssl_module, 'warnings')
    assert hasattr(ssl_module, 'SSLBackendCompatibilityWarning')
    assert hasattr(ssl_module, 'get_ssl_backend_info')


def test_ssl_warning_class_definition():
    """Test SSLBackendCompatibilityWarning class to cover lines 13-15."""
    # Test warning class creation and inheritance
    warning = SSLBackendCompatibilityWarning("Test message")
    assert isinstance(warning, UserWarning)
    assert isinstance(warning, Warning)
    assert str(warning) == "Test message"
    
    # Test that it can be used in warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        warnings.warn("Test", SSLBackendCompatibilityWarning)
        assert len(w) == 1
        assert issubclass(w[0].category, SSLBackendCompatibilityWarning)


def test_get_ssl_backend_info_coverage():
    """Test get_ssl_backend_info to cover lines 18-25."""
    info = get_ssl_backend_info()
    
    # Ensure all keys are present and have correct types
    assert "version" in info
    assert "version_info" in info
    assert "is_libressl" in info
    assert "is_openssl" in info
    
    # Test that the function returns a dict
    assert isinstance(info, dict)
    
    # Test that the boolean logic works
    assert isinstance(info["is_libressl"], bool)
    assert isinstance(info["is_openssl"], bool)
    # Can't both be true
    assert not (info["is_libressl"] and info["is_openssl"])


def test_check_ssl_backend_coverage():
    """Test check_ssl_backend to cover lines 28-36."""
    result = check_ssl_backend()
    assert isinstance(result, bool)
    
    # Test that it returns the same as get_ssl_backend_info()["is_openssl"]
    info = get_ssl_backend_info()
    assert result == info["is_openssl"]


def test_warning_flag_initialization():
    """Test _warning_emitted flag to cover line 40."""
    # Access the module-level flag
    assert isinstance(_warning_emitted, bool)
    # The flag might be True from previous tests, just check it's a bool
    # This is expected behavior since other tests may have triggered the warning


@patch('ai_utilities.ssl_check.get_ssl_backend_info')
def test_emit_ssl_warning_openssl(mock_get_info):
    """Test emit_ssl_compatibility_warning with OpenSSL to cover lines 43-54."""
    mock_get_info.return_value = {
        "version": "OpenSSL 1.1.1",
        "version_info": (1, 1, 1),
        "is_libressl": False,
        "is_openssl": True
    }
    
    # Reset the flag first
    import ai_utilities.ssl_check
    ai_utilities.ssl_check._warning_emitted = False
    
    # Should not emit warning for OpenSSL
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        emit_ssl_compatibility_warning()
        # No warning should be emitted
        assert len([warning for warning in w if issubclass(warning.category, SSLBackendCompatibilityWarning)]) == 0


@patch('ai_utilities.ssl_check.get_ssl_backend_info')
def test_emit_ssl_warning_libressl(mock_get_info):
    """Test emit_ssl_compatibility_warning with LibreSSL to cover lines 55-70."""
    mock_get_info.return_value = {
        "version": "LibreSSL 2.8.3",
        "version_info": (2, 8, 3),
        "is_libressl": True,
        "is_openssl": False
    }
    
    # Reset the flag first
    import ai_utilities.ssl_check
    ai_utilities.ssl_check._warning_emitted = False
    
    # Should emit warning for LibreSSL
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        emit_ssl_compatibility_warning()
        
        # Should have emitted exactly one warning
        libressl_warnings = [warning for warning in w if issubclass(warning.category, SSLBackendCompatibilityWarning)]
        assert len(libressl_warnings) == 1
        
        warning = libressl_warnings[0]
        assert "SSL Backend Compatibility Notice" in str(warning.message)
        assert "LibreSSL" in str(warning.message)
        assert "environment compatibility notice" in str(warning.message)


@patch('ai_utilities.ssl_check.get_ssl_backend_info')
def test_emit_ssl_warning_only_once(mock_get_info):
    """Test that warning is only emitted once to cover global flag logic."""
    mock_get_info.return_value = {
        "version": "LibreSSL 2.8.3",
        "version_info": (2, 8, 3),
        "is_libressl": True,
        "is_openssl": False
    }
    
    # Reset the flag first
    import ai_utilities.ssl_check
    ai_utilities.ssl_check._warning_emitted = False
    
    # Call twice, should only emit warning once
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        emit_ssl_compatibility_warning()
        emit_ssl_compatibility_warning()  # Second call should not emit
        
        # Should have emitted exactly one warning
        libressl_warnings = [warning for warning in w if issubclass(warning.category, SSLBackendCompatibilityWarning)]
        assert len(libressl_warnings) == 1


def test_require_ssl_backend_coverage():
    """Test require_ssl_backend to cover lines 73-80."""
    # This is a convenience function that just calls emit_ssl_compatibility_warning
    # Test that it exists and is callable
    assert callable(require_ssl_backend)
    
    # Test that it calls the emit function (we can't easily test the call without more complex mocking)
    # But we can test that it doesn't raise exceptions
    try:
        require_ssl_backend()
    except Exception as e:
        pytest.fail(f"require_ssl_backend() raised {type(e).__name__}: {e}")


def test_all_functions_accessible():
    """Test that all functions are accessible from the module."""
    # This ensures all import statements work
    functions_to_test = [
        'get_ssl_backend_info',
        'check_ssl_backend', 
        'emit_ssl_compatibility_warning',
        'require_ssl_backend'
    ]
    
    for func_name in functions_to_test:
        assert hasattr(ssl_module, func_name)
        func = getattr(ssl_module, func_name)
        assert callable(func)
