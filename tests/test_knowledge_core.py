"""Comprehensive tests for knowledge base exceptions and models - Phase 7.

This module provides thorough testing for knowledge/exceptions.py and knowledge/models.py,
covering all exception classes, Pydantic models, and their methods.
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock
from hashlib import sha256

from ai_utilities.knowledge.exceptions import (
    KnowledgeError,
    KnowledgeDisabledError,
    SqliteExtensionUnavailableError,
    KnowledgeIndexError,
    KnowledgeSearchError,
    KnowledgeValidationError
)

from ai_utilities.knowledge.models import (
    Source,
    Chunk,
    SearchHit
)


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
    
    def test_knowledge_disabled_error_custom_message(self):
        """Test KnowledgeDisabledError with custom message."""
        error = KnowledgeDisabledError("Custom disabled message")
        
        assert str(error) == "Custom disabled message"
    
    def test_sqlite_extension_error_default_message(self):
        """Test SqliteExtensionUnavailableError with default message."""
        error = SqliteExtensionUnavailableError("vector")
        
        assert isinstance(error, KnowledgeError)
        assert str(error) == "SQLite extension 'vector' is not available"
        assert error.extension_name == "vector"
    
    def test_sqlite_extension_error_custom_message(self):
        """Test SqliteExtensionUnavailableError with custom message."""
        error = SqliteExtensionUnavailableError("vector", "Custom vector error")
        
        assert str(error) == "Custom vector error"
        assert error.extension_name == "vector"
    
    def test_knowledge_index_error_without_cause(self):
        """Test KnowledgeIndexError without cause."""
        error = KnowledgeIndexError("Indexing failed")
        
        assert isinstance(error, KnowledgeError)
        assert str(error) == "Indexing failed"
        assert error.cause is None
    
    def test_knowledge_index_error_with_cause(self):
        """Test KnowledgeIndexError with cause."""
        original_error = ValueError("Original error")
        error = KnowledgeIndexError("Indexing failed", cause=original_error)
        
        assert str(error) == "Indexing failed"
        assert error.cause is original_error
    
    def test_knowledge_search_error_without_cause(self):
        """Test KnowledgeSearchError without cause."""
        error = KnowledgeSearchError("Search failed")
        
        assert isinstance(error, KnowledgeError)
        assert str(error) == "Search failed"
        assert error.cause is None
    
    def test_knowledge_search_error_with_cause(self):
        """Test KnowledgeSearchError with cause."""
        original_error = RuntimeError("Search error")
        error = KnowledgeSearchError("Search failed", cause=original_error)
        
        assert str(error) == "Search failed"
        assert error.cause is original_error
    
    def test_knowledge_validation_error_full(self):
        """Test KnowledgeValidationError with all parameters."""
        error = KnowledgeValidationError(
            "Validation failed",
            field="test_field",
            value="invalid_value"
        )
        
        assert isinstance(error, KnowledgeError)
        assert str(error) == "Validation failed"
        assert error.field == "test_field"
        assert error.value == "invalid_value"
    
    def test_knowledge_validation_error_minimal(self):
        """Test KnowledgeValidationError with minimal parameters."""
        error = KnowledgeValidationError("Validation failed")
        
        assert str(error) == "Validation failed"
        assert error.field is None
        assert error.value is None


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
    
    def test_source_creation_full(self):
        """Test creating a Source with all fields."""
        now = datetime.now()
        source = Source(
            source_id="test_id",
            path=Path("/test/file.py"),
            file_size=2048,
            mime_type="text/x-python",
            loader_type="python",
            git_commit="abc123def",
            mtime=now,
            sha256_hash="def456",
            chunk_count=5,
            indexed_at=now
        )
        
        assert source.loader_type == "python"
        assert source.git_commit == "abc123def"
        assert source.chunk_count == 5
    
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
    
    def test_file_extension_no_extension(self):
        """Test file_extension property when file has no extension."""
        source = Source(
            source_id="test",
            path=Path("/test/file"),
            file_size=100,
            mime_type="application/octet-stream",
            mtime=datetime.now(),
            sha256_hash="abc"
        )
        
        assert source.file_extension == ""
    
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
        
        # Test non-text file
        source = Source(
            source_id="test",
            path=Path("/test/file.pdf"),
            file_size=100,
            mime_type="application/pdf",
            mtime=datetime.now(),
            sha256_hash="abc"
        )
        assert source.is_text_file is False
    
    def test_source_creation_basic(self):
        """Test basic Source creation without subprocess calls."""
        source = Source(
            source_id="test_id",
            path=Path("/test/file.py"),
            file_size=1024,
            mime_type="text/x-python",
            loader_type="python",
            mtime=datetime.now(),
            sha256_hash="abc123",
            git_commit="def456"
        )
        
        assert source.source_id == "test_id"
        assert source.path == Path("/test/file.py")
        assert source.file_size == 1024
        assert source.mime_type == "text/x-python"
        assert source.loader_type == "python"
        assert source.git_commit == "def456"
        assert source.chunk_count == 0
    
    def test_source_file_extension_detection(self):
        """Test file extension detection for various file types."""
        test_cases = [
            ("file.md", "md"),
            ("file.txt", "txt"),
            ("file.py", "py"),
            ("file.PY", "py"),  # Test case conversion
            ("file", ""),        # No extension
        ]
        
        for filename, expected_ext in test_cases:
            source = Source(
                source_id="test",
                path=Path(f"/test/{filename}"),
                file_size=100,
                mime_type="text/plain",
                mtime=datetime.now(),
                sha256_hash="abc"
            )
            assert source.file_extension == expected_ext
    
    def test_source_is_text_file_detection(self):
        """Test text file detection."""
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
        
        # Test non-text file
        source = Source(
            source_id="test",
            path=Path("/test/file.pdf"),
            file_size=100,
            mime_type="application/pdf",
            mtime=datetime.now(),
            sha256_hash="abc"
        )
        assert source.is_text_file is False


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
        assert chunk.text == "Test chunk content"
        assert chunk.chunk_index == 0
        assert chunk.start_char == 0
        assert chunk.end_char == 18
        assert chunk.metadata == {}  # Default
        assert chunk.embedding is None  # Default
    
    def test_chunk_creation_full(self):
        """Test creating a Chunk with all fields."""
        now = datetime.now()
        embedding = [0.1, 0.2, 0.3]
        
        chunk = Chunk(
            chunk_id="chunk_1",
            source_id="source_1",
            text="Test chunk content",
            metadata={"section": "intro"},
            chunk_index=0,
            start_char=0,
            end_char=18,
            embedding=embedding,
            embedding_model="text-embedding-ada-002",
            embedded_at=now,
            embedding_dimensions=3
        )
        
        assert chunk.metadata == {"section": "intro"}
        assert chunk.embedding == embedding
        assert chunk.embedding_model == "text-embedding-ada-002"
        assert chunk.embedded_at == now
        assert chunk.embedding_dimensions == 3
    
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
    
    def test_has_embedding_property(self):
        """Test the has_embedding computed property."""
        # Chunk with embedding
        chunk_with_embedding = Chunk(
            chunk_id="chunk_1",
            source_id="source_1",
            text="Test",
            chunk_index=0,
            start_char=0,
            end_char=4,
            embedding=[0.1, 0.2, 0.3]
        )
        assert chunk_with_embedding.has_embedding is True
        
        # Chunk without embedding
        chunk_without_embedding = Chunk(
            chunk_id="chunk_2",
            source_id="source_1",
            text="Test",
            chunk_index=1,
            start_char=5,
            end_char=9
        )
        assert chunk_without_embedding.has_embedding is False
        
        # Chunk with empty embedding
        chunk_empty_embedding = Chunk(
            chunk_id="chunk_3",
            source_id="source_1",
            text="Test",
            chunk_index=2,
            start_char=10,
            end_char=14,
            embedding=[]
        )
        assert chunk_empty_embedding.has_embedding is False
    
    def test_embedding_dimension_property(self):
        """Test the embedding_dimension computed property."""
        # Chunk with embedding
        chunk_with_embedding = Chunk(
            chunk_id="chunk_1",
            source_id="source_1",
            text="Test",
            chunk_index=0,
            start_char=0,
            end_char=4,
            embedding=[0.1, 0.2, 0.3, 0.4]
        )
        assert chunk_with_embedding.embedding_dimension == 4
        
        # Chunk without embedding
        chunk_without_embedding = Chunk(
            chunk_id="chunk_2",
            source_id="source_1",
            text="Test",
            chunk_index=1,
            start_char=5,
            end_char=9
        )
        assert chunk_without_embedding.embedding_dimension is None


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
        assert hit.text == "Search result text"
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
        
        # Edge case
        edge_hit = SearchHit(
            chunk=chunk,
            text="test",
            similarity_score=0.8,
            rank=3,
            source_path=Path("/test"),
            source_type="txt"
        )
        assert edge_hit.is_high_similarity is False
    
    def test_is_medium_similarity_property(self):
        """Test the is_medium_similarity computed property."""
        chunk = Chunk(
            chunk_id="chunk_1",
            source_id="source_1",
            text="test",
            chunk_index=0,
            start_char=0,
            end_char=4
        )
        
        # Medium similarity (lower bound)
        medium_low = SearchHit(
            chunk=chunk,
            text="test",
            similarity_score=0.5,
            rank=1,
            source_path=Path("/test"),
            source_type="txt"
        )
        assert medium_low.is_medium_similarity is True
        
        # Medium similarity (upper bound)
        medium_high = SearchHit(
            chunk=chunk,
            text="test",
            similarity_score=0.8,
            rank=2,
            source_path=Path("/test"),
            source_type="txt"
        )
        assert medium_high.is_medium_similarity is True
        
        # Below medium
        low_hit = SearchHit(
            chunk=chunk,
            text="test",
            similarity_score=0.4,
            rank=3,
            source_path=Path("/test"),
            source_type="txt"
        )
        assert low_hit.is_medium_similarity is False
        
        # Above medium
        high_hit = SearchHit(
            chunk=chunk,
            text="test",
            similarity_score=0.9,
            rank=4,
            source_path=Path("/test"),
            source_type="txt"
        )
        assert high_hit.is_medium_similarity is False
    
    def test_from_chunk_with_path_string(self):
        """Test SearchHit.from_chunk with string path."""
        chunk = Chunk(
            chunk_id="chunk_1",
            source_id="source_1",
            text="Test content",
            chunk_index=0,
            start_char=0,
            end_char=12
        )
        
        hit = SearchHit.from_chunk(
            chunk=chunk,
            similarity_score=0.75,
            rank=1,
            source_path="/test/file.py"
        )
        
        assert hit.chunk == chunk
        assert hit.text == "Test content"
        assert hit.similarity_score == 0.75
        assert hit.rank == 1
        assert hit.source_path == Path("/test/file.py")
        assert hit.source_type == "py"
    
    def test_from_chunk_with_path_object(self):
        """Test SearchHit.from_chunk with Path object."""
        chunk = Chunk(
            chunk_id="chunk_1",
            source_id="source_1",
            text="Test content",
            chunk_index=0,
            start_char=0,
            end_char=12
        )
        
        hit = SearchHit.from_chunk(
            chunk=chunk,
            similarity_score=0.75,
            rank=1,
            source_path=Path("/test/file.md")
        )
        
        assert hit.source_path == Path("/test/file.md")
        assert hit.source_type == "md"
    
    def test_from_chunk_edge_cases(self):
        """Test SearchHit.from_chunk with edge cases."""
        chunk = Chunk(
            chunk_id="chunk_1",
            source_id="source_1",
            text="Test",
            chunk_index=0,
            start_char=0,
            end_char=4
        )
        
        # Test with file that has no extension
        hit = SearchHit.from_chunk(
            chunk=chunk,
            similarity_score=0.5,
            rank=1,
            source_path=Path("/test/file")
        )
        
        assert hit.source_type == ""
        
        # Test with uppercase extension
        hit = SearchHit.from_chunk(
            chunk=chunk,
            similarity_score=0.5,
            rank=2,
            source_path=Path("/test/file.PY")
        )
        
        assert hit.source_type == "py"


class TestModelValidation:
    """Test Pydantic model validation."""
    
    def test_source_validation_required_fields(self):
        """Test that Source requires all required fields."""
        # Missing required fields should raise validation error
        with pytest.raises(ValueError):  # Pydantic raises ValidationError
            Source(
                source_id="test",
                # Missing path, file_size, mime_type, mtime, sha256_hash
            )
    
    def test_chunk_validation_required_fields(self):
        """Test that Chunk requires all required fields."""
        with pytest.raises(ValueError):  # Pydantic raises ValidationError
            Chunk(
                chunk_id="test",
                # Missing source_id, text, chunk_index, start_char, end_char
            )
    
    def test_search_hit_validation_required_fields(self):
        """Test that SearchHit requires all required fields."""
        chunk = Chunk(
            chunk_id="chunk_1",
            source_id="source_1",
            text="Test",
            chunk_index=0,
            start_char=0,
            end_char=4
        )
        
        with pytest.raises(ValueError):  # Pydantic raises ValidationError
            SearchHit(
                chunk=chunk,
                # Missing text, similarity_score, rank, source_path, source_type
            )
    
    def test_similarity_score_validation(self):
        """Test SearchHit similarity score validation."""
        chunk = Chunk(
            chunk_id="chunk_1",
            source_id="source_1",
            text="Test",
            chunk_index=0,
            start_char=0,
            end_char=4
        )
        
        # Valid scores
        for score in [0.0, 0.5, 1.0]:
            hit = SearchHit(
                chunk=chunk,
                text="test",
                similarity_score=score,
                rank=1,
                source_path=Path("/test"),
                source_type="txt"
            )
            assert hit.similarity_score == score
