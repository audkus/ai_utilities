"""
Tests for knowledge/models.py module.
"""

import pytest
from datetime import datetime
from pathlib import Path

from ai_utilities.knowledge.models import Source, Chunk, SearchHit


class TestSource:
    """Test Source model."""
    
    def test_source_creation_minimal(self):
        """Test creating Source with minimal required fields."""
        source = Source(
            source_id="test_123",
            path=Path("/test/file.md"),
            file_size=1024,
            mime_type="text/markdown",
            mtime=datetime(2023, 1, 1, 12, 0, 0),
            sha256_hash="abc123def456"
        )
        
        assert source.source_id == "test_123"
        assert source.path == Path("/test/file.md")
        assert source.file_size == 1024
        assert source.mime_type == "text/markdown"
        assert source.mtime == datetime(2023, 1, 1, 12, 0, 0)
        assert source.sha256_hash == "abc123def456"
        assert source.loader_type is None
        assert source.git_commit is None
        assert source.indexed_at is not None
        assert source.chunk_count == 0
    
    def test_file_extension_property(self):
        """Test file_extension computed property."""
        test_cases = [
            (Path("file.md"), "md"),
            (Path("file.txt"), "txt"),
            (Path("file.py"), "py"),
            (Path("file"), ""),
            (Path("file.JSON"), "json"),
            (Path(".hidden"), ""),
        ]
        
        for path, expected in test_cases:
            source = Source(
                source_id="test",
                path=path,
                file_size=100,
                mime_type="text/plain",
                mtime=datetime.now(),
                sha256_hash="abc123"
            )
            assert source.file_extension == expected
    
    def test_is_text_file_property(self):
        """Test is_text_file computed property."""
        text_extensions = ["md", "txt", "py", "log", "rst", "yaml", "yml", "json"]
        
        for ext in text_extensions:
            source = Source(
                source_id="test",
                path=Path(f"file.{ext}"),
                file_size=100,
                mime_type="text/plain",
                mtime=datetime.now(),
                sha256_hash="abc123"
            )
            assert source.is_text_file is True
        
        source = Source(
            source_id="test",
            path=Path("file.pdf"),
            file_size=100,
            mime_type="application/pdf",
            mtime=datetime.now(),
            sha256_hash="abc123"
        )
        assert source.is_text_file is False


class TestChunk:
    """Test Chunk model."""
    
    def test_chunk_creation_minimal(self):
        """Test creating Chunk with minimal required fields."""
        chunk = Chunk(
            chunk_id="chunk_123",
            source_id="source_456",
            text="This is a test chunk of text.",
            chunk_index=0,
            start_char=0,
            end_char=31
        )
        
        assert chunk.chunk_id == "chunk_123"
        assert chunk.source_id == "source_456"
        assert chunk.text == "This is a test chunk of text."
        assert chunk.chunk_index == 0
        assert chunk.start_char == 0
        assert chunk.end_char == 31
        assert chunk.embedding is None
        assert chunk.embedding_model is None
        assert chunk.embedded_at is None
        assert chunk.embedding_dimensions is None
        assert chunk.metadata == {}
    
    def test_chunk_creation_with_embedding(self):
        """Test creating Chunk with embedding."""
        embedded_at = datetime(2023, 1, 1, 12, 0, 0)
        chunk = Chunk(
            chunk_id="chunk_789",
            source_id="source_123",
            text="Another test chunk.",
            metadata={"section": "intro"},
            chunk_index=1,
            start_char=0,
            end_char=20,
            embedding=[0.1, 0.2, 0.3],
            embedding_model="text-embedding-ada-002",
            embedded_at=embedded_at,
            embedding_dimensions=3
        )
        
        assert chunk.embedding == [0.1, 0.2, 0.3]
        assert chunk.embedding_model == "text-embedding-ada-002"
        assert chunk.embedded_at == embedded_at
        assert chunk.embedding_dimensions == 3
    
    def test_text_length_property(self):
        """Test text_length computed property."""
        chunk = Chunk(
            chunk_id="test",
            source_id="source",
            text="12345",
            chunk_index=0,
            start_char=0,
            end_char=5
        )
        assert chunk.text_length == 5
        
        empty_chunk = Chunk(
            chunk_id="empty",
            source_id="source",
            text="",
            chunk_index=0,
            start_char=0,
            end_char=0
        )
        assert empty_chunk.text_length == 0
    
    def test_has_embedding_property(self):
        """Test has_embedding computed property."""
        chunk_with_embedding = Chunk(
            chunk_id="test1",
            source_id="source",
            text="test",
            chunk_index=0,
            start_char=0,
            end_char=4,
            embedding=[0.1, 0.2]
        )
        assert chunk_with_embedding.has_embedding is True
        
        chunk_without_embedding = Chunk(
            chunk_id="test2",
            source_id="source",
            text="test",
            chunk_index=0,
            start_char=0,
            end_char=4
        )
        assert chunk_without_embedding.has_embedding is False
        
        chunk_empty_embedding = Chunk(
            chunk_id="test3",
            source_id="source",
            text="test",
            chunk_index=0,
            start_char=0,
            end_char=4,
            embedding=[]
        )
        assert chunk_empty_embedding.has_embedding is False
    
    def test_embedding_dimension_property(self):
        """Test embedding_dimension computed property."""
        chunk = Chunk(
            chunk_id="test",
            source_id="source",
            text="test",
            chunk_index=0,
            start_char=0,
            end_char=4,
            embedding=[0.1, 0.2, 0.3]
        )
        assert chunk.embedding_dimension == 3
        
        chunk_no_embedding = Chunk(
            chunk_id="test2",
            source_id="source",
            text="test",
            chunk_index=0,
            start_char=0,
            end_char=4
        )
        assert chunk_no_embedding.embedding_dimension is None


class TestSearchHit:
    """Test SearchHit model."""
    
    def test_search_hit_creation(self):
        """Test creating SearchHit."""
        chunk = Chunk(
            chunk_id="chunk_123",
            source_id="source_456",
            text="This is a test chunk.",
            chunk_index=0,
            start_char=0,
            end_char=21
        )
        
        hit = SearchHit(
            chunk=chunk,
            text="This is a test chunk.",
            similarity_score=0.85,
            rank=1,
            source_path=Path("/test/file.md"),
            source_type="text/markdown"
        )
        
        assert hit.chunk == chunk
        assert hit.text == "This is a test chunk."
        assert hit.similarity_score == 0.85
        assert hit.rank == 1
        assert hit.source_path == Path("/test/file.md")
        assert hit.source_type == "text/markdown"
    
    def test_similarity_score_bounds(self):
        """Test that similarity_score is within expected bounds."""
        chunk = Chunk(
            chunk_id="test",
            source_id="source",
            text="test",
            chunk_index=0,
            start_char=0,
            end_char=4
        )
        
        valid_scores = [0.0, 0.5, 1.0, 0.999]
        for score in valid_scores:
            hit = SearchHit(
                chunk=chunk,
                text="test",
                similarity_score=score,
                rank=1,
                source_path=Path("/test/file.md"),
                source_type="text/plain"
            )
            assert 0.0 <= hit.similarity_score <= 1.0


class TestModelValidation:
    """Test model validation."""
    
    def test_source_validation_errors(self):
        """Test Source model validation errors."""
        with pytest.raises(Exception):
            Source(source_id="test")
    
    def test_chunk_validation_errors(self):
        """Test Chunk model validation errors."""
        with pytest.raises(Exception):
            Chunk(chunk_id="test")
    
    def test_search_hit_validation_errors(self):
        """Test SearchHit model validation errors."""
        chunk = Chunk(
            chunk_id="test",
            source_id="source",
            text="test",
            chunk_index=0,
            start_char=0,
            end_char=4
        )
        
        with pytest.raises(Exception):
            SearchHit(chunk=chunk)


class TestModelInheritance:
    """Test that all models inherit from BaseModel."""
    
    def test_all_models_are_pydantic(self):
        """Test that all models are Pydantic models."""
        models = [Source, Chunk, SearchHit]
        
        for model in models:
            assert hasattr(model, 'model_dump') or hasattr(model, 'dict')
            assert hasattr(model, 'model_validate') or hasattr(model, 'parse_obj')
