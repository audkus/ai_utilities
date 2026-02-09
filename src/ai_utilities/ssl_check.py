"""
SSL Backend Compatibility Checker

This module provides utilities to check SSL backend compatibility
and emit appropriate warnings for unsupported configurations.
"""

import ssl
import warnings
from typing import Optional


class SSLBackendCompatibilityWarning(UserWarning):
    """Warning for SSL backend compatibility issues."""
    pass


def get_ssl_backend_info() -> dict:
    """Get information about the current SSL backend."""
    return {
        "version": ssl.OPENSSL_VERSION,
        "version_info": ssl.OPENSSL_VERSION_INFO,
        "is_libressl": "LibreSSL" in ssl.OPENSSL_VERSION,
        "is_openssl": "OpenSSL" in ssl.OPENSSL_VERSION and "LibreSSL" not in ssl.OPENSSL_VERSION,
    }


def check_ssl_backend() -> bool:
    """
    Check if the current SSL backend is supported.
    
    Returns:
        bool: True if OpenSSL is detected, False if LibreSSL is detected
    """
    info = get_ssl_backend_info()
    return info["is_openssl"]


# Module-level flag to ensure warning is emitted at most once per process
_warning_emitted = False


def emit_ssl_compatibility_warning() -> None:
    """
    Emit a warning if LibreSSL is detected.
    
    This function ensures the warning is emitted at most once per process.
    The warning clearly states this is an environment compatibility notice,
    not a bug in ai_utilities, and that network functionality may be affected.
    """
    global _warning_emitted
    
    if _warning_emitted:
        return
    
    info = get_ssl_backend_info()
    
    if info["is_libressl"]:
        _warning_emitted = True
        warnings.warn(
            f"SSL Backend Compatibility Notice: Detected LibreSSL ({info['version']}). "
            f"This is an environment compatibility notice, not a bug in ai_utilities. "
            f"ai_utilities requires OpenSSL ≥ 1.1.1 for reliable HTTPS operations. "
            f"urllib3 v2 (used by requests) may have compatibility issues with LibreSSL. "
            f"Network functionality may be affected. "
            f"To fix: Use Python linked against OpenSSL (python.org, Homebrew, pyenv). "
            f"See documentation for troubleshooting guidance.",
            SSLBackendCompatibilityWarning,
            stacklevel=2
        )


def require_ssl_backend() -> None:
    """
    Check SSL backend and emit warning if needed.
    
    This is a convenience function that can be called at library entry points.
    """
    emit_ssl_compatibility_warning()
