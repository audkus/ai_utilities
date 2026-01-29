"""
Tests for knowledge/exceptions.py module.
"""

import pytest

from ai_utilities.knowledge.exceptions import (
    KnowledgeError,
    KnowledgeDisabledError,
    SqliteExtensionUnavailableError,
    KnowledgeIndexError,
    KnowledgeSearchError,
    KnowledgeValidationError
)


class TestKnowledgeError:
    """Test base KnowledgeError exception."""
    
    def test_knowledge_error_inheritance(self):
        """Test that KnowledgeError inherits from Exception."""
        assert issubclass(KnowledgeError, Exception)
    
    def test_knowledge_error_creation(self):
        """Test creating KnowledgeError."""
        error = KnowledgeError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)


class TestKnowledgeDisabledError:
    """Test KnowledgeDisabledError exception."""
    
    def test_inheritance(self):
        """Test that KnowledgeDisabledError inherits from KnowledgeError."""
        assert issubclass(KnowledgeDisabledError, KnowledgeError)
    
    def test_default_message(self):
        """Test default error message."""
        error = KnowledgeDisabledError()
        assert str(error) == "Knowledge functionality is disabled"
    
    def test_custom_message(self):
        """Test custom error message."""
        error = KnowledgeDisabledError("Custom disabled message")
        assert str(error) == "Custom disabled message"


class TestSqliteExtensionUnavailableError:
    """Test SqliteExtensionUnavailableError exception."""
    
    def test_inheritance(self):
        """Test that SqliteExtensionUnavailableError inherits from KnowledgeError."""
        assert issubclass(SqliteExtensionUnavailableError, KnowledgeError)
    
    def test_default_message(self):
        """Test default error message."""
        error = SqliteExtensionUnavailableError("vector")
        assert str(error) == "SQLite extension 'vector' is not available"
        assert error.extension_name == "vector"
    
    def test_custom_message(self):
        """Test custom error message."""
        error = SqliteExtensionUnavailableError("vector", "Custom vector error")
        assert str(error) == "Custom vector error"
        assert error.extension_name == "vector"


class TestKnowledgeIndexError:
    """Test KnowledgeIndexError exception."""
    
    def test_inheritance(self):
        """Test that KnowledgeIndexError inherits from KnowledgeError."""
        assert issubclass(KnowledgeIndexError, KnowledgeError)
    
    def test_error_creation(self):
        """Test creating KnowledgeIndexError."""
        error = KnowledgeIndexError("Indexing failed")
        assert str(error) == "Indexing failed"
        assert error.cause is None
    
    def test_error_with_cause(self):
        """Test KnowledgeIndexError with cause."""
        cause = ValueError("Invalid data")
        error = KnowledgeIndexError("Indexing failed", cause)
        assert str(error) == "Indexing failed"
        assert error.cause == cause


class TestKnowledgeSearchError:
    """Test KnowledgeSearchError exception."""
    
    def test_inheritance(self):
        """Test that KnowledgeSearchError inherits from KnowledgeError."""
        assert issubclass(KnowledgeSearchError, KnowledgeError)
    
    def test_error_creation(self):
        """Test creating KnowledgeSearchError."""
        error = KnowledgeSearchError("Search failed")
        assert str(error) == "Search failed"
        assert error.cause is None
    
    def test_error_with_cause(self):
        """Test KnowledgeSearchError with cause."""
        cause = RuntimeError("Database error")
        error = KnowledgeSearchError("Search failed", cause)
        assert str(error) == "Search failed"
        assert error.cause == cause


class TestKnowledgeValidationError:
    """Test KnowledgeValidationError exception."""
    
    def test_inheritance(self):
        """Test that KnowledgeValidationError inherits from KnowledgeError."""
        assert issubclass(KnowledgeValidationError, KnowledgeError)
    
    def test_error_creation(self):
        """Test creating KnowledgeValidationError."""
        error = KnowledgeValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert error.field is None
        assert error.value is None
    
    def test_error_with_field_and_value(self):
        """Test KnowledgeValidationError with field and value."""
        error = KnowledgeValidationError("Invalid field", "title", "invalid_title")
        assert str(error) == "Invalid field"
        assert error.field == "title"
        assert error.value == "invalid_title"


class TestExceptionHierarchy:
    """Test the overall exception hierarchy."""
    
    def test_all_exceptions_inherit_from_knowledge_error(self):
        """Test that all knowledge exceptions inherit from KnowledgeError."""
        exceptions = [
            KnowledgeDisabledError,
            SqliteExtensionUnavailableError,
            KnowledgeIndexError,
            KnowledgeSearchError,
            KnowledgeValidationError
        ]
        
        for exc in exceptions:
            assert issubclass(exc, KnowledgeError)
            assert issubclass(exc, Exception)
    
    def test_exception_catching(self):
        """Test that exceptions can be caught properly."""
        # Test catching base KnowledgeError
        try:
            raise KnowledgeDisabledError()
        except KnowledgeError as e:
            assert isinstance(e, KnowledgeDisabledError)
        
        # Test catching specific exception
        try:
            raise SqliteExtensionUnavailableError("vector")
        except SqliteExtensionUnavailableError as e:
            assert e.extension_name == "vector"
