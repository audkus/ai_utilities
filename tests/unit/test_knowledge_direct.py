"""Direct tests for knowledge base exceptions and models - Phase 7.

This module tests knowledge modules by importing directly from specific files
to avoid circular dependencies and blocking imports.
"""

import pytest
from datetime import datetime
from pathlib import Path

# Import directly from specific modules to avoid circular dependencies
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_utilities.knowledge.exceptions import (
    KnowledgeError,
    KnowledgeDisabledError,
    SqliteExtensionUnavailableError,
    KnowledgeIndexError,
    KnowledgeSearchError,
    KnowledgeValidationError
)

# Test that we can import models without issues
try:
    from ai_utilities.knowledge.models import (
        Source,
        Chunk,
        SearchHit
    )
    MODELS_AVAILABLE = True
except ImportError as e:
    print(f"Models import failed: {e}")
    MODELS_AVAILABLE = False


@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models module not available")
class TestKnowledgeExceptions:
    """Test knowledge module exception hierarchy and functionality."""
    
    def test_knowledge_error_base_class(self):
        """Test the base KnowledgeError exception."""
        error = KnowledgeError("Base knowledge error")
        assert isinstance(error, Exception)
        assert str(error) == "Base knowledge error"
    
    def test_knowledge_disabled_error_default(self):
        """Test KnowledgeDisabledError with default message."""
        error = KnowledgeDisabledError()
        assert isinstance(error, KnowledgeError)
        assert str(error) == "Knowledge functionality is disabled"
    
    def test_sqlite_extension_error(self):
        """Test SqliteExtensionUnavailableError."""
        error = SqliteExtensionUnavailableError("vector")
        assert isinstance(error, KnowledgeError)
        assert str(error) == "SQLite extension 'vector' is not available"
        assert error.extension_name == "vector"
    
    def test_knowledge_index_error(self):
        """Test KnowledgeIndexError."""
        error = KnowledgeIndexError("Indexing failed")
        assert isinstance(error, KnowledgeError)
        assert str(error) == "Indexing failed"
        assert error.cause is None
    
    def test_knowledge_search_error(self):
        """Test KnowledgeSearchError."""
        error = KnowledgeSearchError("Search failed")
        assert isinstance(error, KnowledgeError)
        assert str(error) == "Search failed"
        assert error.cause is None
    
    def test_knowledge_validation_error(self):
        """Test KnowledgeValidationError."""
        error = KnowledgeValidationError(
            "Validation failed",
            field="test_field",
            value="invalid_value"
        )
        assert isinstance(error, KnowledgeError)
        assert str(error) == "Validation failed"
        assert error.field == "test_field"
        assert error.value == "invalid_value"


@pytest.mark.optional_dep
@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models module not available")
class TestSourceModel:
    """Test the Source Pydantic model."""
    
    def test_source_creation_minimal(self):
        """Test creating a Source with minimal required fields."""
        source = Source(
            source_id="test_id",
            path=Path("/test/file.md"),
            file_size=1024,
            mime_type="text/markdown",
            mtime=datetime.now(),
            sha256_hash="abc123"
        )
        
        assert source.source_id == "test_id"
        assert source.path == Path("/test/file.md")
        assert source.file_size == 1024
        assert source.mime_type == "text/markdown"
        assert source.chunk_count == 0  # Default value
        assert source.loader_type is None  # Default value
    
    def test_file_extension_property(self):
        """Test the file_extension computed property."""
        source = Source(
            source_id="test",
            path=Path("/test/file.MD"),
            file_size=100,
            mime_type="text/markdown",
            mtime=datetime.now(),
            sha256_hash="abc"
        )
        
        assert source.file_extension == "md"
    
    def test_is_text_file_property(self):
        """Test the is_text_file computed property."""
        text_extensions = ['md', 'txt', 'py', 'log', 'rst', 'yaml', 'yml', 'json']
        
        for ext in text_extensions:
            source = Source(
                source_id="test",
                path=Path(f"/test/file.{ext}"),
                file_size=100,
                mime_type="text/plain",
                mtime=datetime.now(),
                sha256_hash="abc"
            )
            assert source.is_text_file is True


@pytest.mark.optional_dep
@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models module not available")
class TestChunkModel:
    """Test the Chunk Pydantic model."""
    
    def test_chunk_creation_minimal(self):
        """Test creating a Chunk with minimal required fields."""
        chunk = Chunk(
            chunk_id="chunk_1",
            source_id="source_1",
            text="Test chunk content",
            chunk_index=0,
            start_char=0,
            end_char=18
        )
        
        assert chunk.chunk_id == "chunk_1"
        assert chunk.source_id == "source_1"
        assert isinstance(chunk.text, str)  # Contract: text is string type
        assert len(chunk.text) > 0  # Contract: non-empty text
        assert chunk.chunk_index == 0
        assert chunk.start_char == 0
        assert chunk.end_char == 18
        assert chunk.metadata == {}  # Default
        assert chunk.embedding is None  # Default
    
    def test_text_length_property(self):
        """Test the text_length computed property."""
        chunk = Chunk(
            chunk_id="chunk_1",
            source_id="source_1",
            text="Hello, world!",
            chunk_index=0,
            start_char=0,
            end_char=13
        )
        
        assert chunk.text_length == 13


@pytest.mark.optional_dep
@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models module not available")
class TestSearchHitModel:
    """Test the SearchHit Pydantic model."""
    
    def test_search_hit_creation(self):
        """Test creating a SearchHit."""
        chunk = Chunk(
            chunk_id="chunk_1",
            source_id="source_1",
            text="Search result text",
            chunk_index=0,
            start_char=0,
            end_char=18
        )
        
        hit = SearchHit(
            chunk=chunk,
            text="Search result text",
            similarity_score=0.85,
            rank=1,
            source_path=Path("/test/file.md"),
            source_type="md"
        )
        
        assert hit.chunk == chunk
        assert isinstance(hit.text, str)  # Contract: text is string type
        assert len(hit.text) > 0  # Contract: non-empty text
        assert hit.similarity_score == 0.85
        assert hit.rank == 1
        assert hit.source_path == Path("/test/file.md")
        assert hit.source_type == "md"
    
    def test_is_high_similarity_property(self):
        """Test the is_high_similarity computed property."""
        chunk = Chunk(
            chunk_id="chunk_1",
            source_id="source_1",
            text="test",
            chunk_index=0,
            start_char=0,
            end_char=4
        )
        
        # High similarity
        high_hit = SearchHit(
            chunk=chunk,
            text="test",
            similarity_score=0.9,
            rank=1,
            source_path=Path("/test"),
            source_type="txt"
        )
        assert high_hit.is_high_similarity is True
        
        # Not high similarity
        low_hit = SearchHit(
            chunk=chunk,
            text="test",
            similarity_score=0.7,
            rank=2,
            source_path=Path("/test"),
            source_type="txt"
        )
        assert low_hit.is_high_similarity is False
