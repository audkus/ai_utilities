"""Test knowledge module imports work correctly."""

import pytest


def test_knowledge_exceptions_import():
    """Test that knowledge exceptions can be imported."""
    from ai_utilities.knowledge.exceptions import (
        KnowledgeError,
        KnowledgeDisabledError,
        SqliteExtensionUnavailableError,
        KnowledgeIndexError,
        KnowledgeSearchError,
        KnowledgeValidationError
    )
    
    # Verify all exceptions are available and inherit from KnowledgeError
    assert issubclass(KnowledgeDisabledError, KnowledgeError)
    assert issubclass(SqliteExtensionUnavailableError, KnowledgeError)
    assert issubclass(KnowledgeIndexError, KnowledgeError)
    assert issubclass(KnowledgeSearchError, KnowledgeError)
    assert issubclass(KnowledgeValidationError, KnowledgeError)


def test_knowledge_models_import():
    """Test that knowledge models can be imported."""
    from ai_utilities.knowledge.models import Source, Chunk, SearchHit
    
    # Verify all models are available
    assert Source is not None
    assert Chunk is not None
    assert SearchHit is not None


def test_knowledge_backend_import():
    """Test that knowledge backend can be imported."""
    from ai_utilities.knowledge.backend import SqliteVectorBackend
    
    # Verify backend is available
    assert SqliteVectorBackend is not None


def test_knowledge_indexer_import():
    """Test that knowledge indexer can be imported."""
    from ai_utilities.knowledge.indexer import KnowledgeIndexer
    
    # Verify indexer is available
    assert KnowledgeIndexer is not None


def test_knowledge_search_import():
    """Test that knowledge search can be imported."""
    from ai_utilities.knowledge.search import KnowledgeSearch
    
    # Verify search is available
    assert KnowledgeSearch is not None


def test_knowledge_sources_import():
    """Test that knowledge sources can be imported."""
    from ai_utilities.knowledge.sources import FileSourceLoader
    
    # Verify sources are available
    assert FileSourceLoader is not None


def test_knowledge_chunking_import():
    """Test that knowledge chunking can be imported."""
    from ai_utilities.knowledge.chunking import TextChunker
    
    # Verify chunking is available
    assert TextChunker is not None


def test_all_knowledge_modules_import():
    """Test that all knowledge modules can be imported without circular dependencies."""
    # This test ensures there are no circular import issues
    import ai_utilities.knowledge.exceptions
    import ai_utilities.knowledge.models
    import ai_utilities.knowledge.backend
    import ai_utilities.knowledge.indexer
    import ai_utilities.knowledge.search
    import ai_utilities.knowledge.sources
    import ai_utilities.knowledge.chunking
    
    # If we reach this point, all imports succeeded
    assert True
