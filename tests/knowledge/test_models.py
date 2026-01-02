"""
Tests for knowledge models.

Tests the Pydantic models used throughout the knowledge system.
"""

from __future__ import annotations

import pytest
from datetime import datetime
from pathlib import Path

from ai_utilities.knowledge.models import Source, Chunk, SearchHit


class TestSource:
    """Test the Source model."""
    
    def test_source_creation(self) -> None:
        """Test creating a source with valid data."""
        source = Source(
            source_id="test_source",
            path=Path("/test/file.txt"),
            file_size=1024,
            mime_type="text/plain",
            mtime=datetime.now(),
            sha256_hash="abcd1234",
        )
        
        assert source.source_id == "test_source"
        assert source.path == Path("/test/file.txt")
        assert source.file_size == 1024
        assert source.mime_type == "text/plain"
        assert source.file_extension == "txt"
        assert source.is_text_file is True
    
    def test_source_from_path(self, tmp_path) -> None:
        """Test creating a source from a file path."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!")
        
        source = Source.from_path(test_file)
        
        assert source.source_id == str(test_file)
        assert source.path == test_file.absolute()
        assert source.file_size > 0
        assert source.mime_type == "text/plain"
        assert source.file_extension == "txt"
        assert source.is_text_file is True
        assert len(source.sha256_hash) == 64  # SHA256 hex length
    
    def test_source_nonexistent_file(self) -> None:
        """Test creating a source from a non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            Source.from_path(Path("/nonexistent/file.txt"))
    
    def test_file_extensions(self) -> None:
        """Test file extension detection."""
        test_cases = [
            ("test.md", "md", True),
            ("test.txt", "txt", True),
            ("test.py", "py", True),
            ("test.log", "log", True),
            ("test.unknown", "unknown", False),
        ]
        
        for filename, expected_ext, expected_is_text in test_cases:
            source = Source(
                source_id="test",
                path=Path(f"/test/{filename}"),
                file_size=100,
                mime_type="text/plain",
                mtime=datetime.now(),
                sha256_hash="abcd1234",
            )
            
            assert source.file_extension == expected_ext
            assert source.is_text_file == expected_is_text


class TestChunk:
    """Test the Chunk model."""
    
    def test_chunk_creation(self) -> None:
        """Test creating a chunk with valid data."""
        chunk = Chunk(
            chunk_id="test_chunk",
            source_id="test_source",
            text="This is a test chunk.",
            chunk_index=0,
            start_char=0,
            end_char=22,
        )
        
        assert chunk.chunk_id == "test_chunk"
        assert chunk.source_id == "test_source"
        assert chunk.text == "This is a test chunk."
        assert chunk.text_length == 21
        assert chunk.chunk_index == 0
        assert chunk.start_char == 0
        assert chunk.end_char == 22
        assert chunk.has_embedding is False
        assert chunk.embedding_dimension is None
    
    def test_chunk_with_embedding(self) -> None:
        """Test creating a chunk with an embedding."""
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        chunk = Chunk(
            chunk_id="test_chunk",
            source_id="test_source",
            text="Test chunk",
            chunk_index=0,
            start_char=0,
            end_char=10,
            embedding=embedding,
            embedding_model="test-model",
            embedded_at=datetime.now(),
        )
        
        assert chunk.has_embedding is True
        assert chunk.embedding_dimension == 5
        assert chunk.embedding == embedding
        assert chunk.embedding_model == "test-model"
        assert chunk.embedded_at is not None
    
    def test_chunk_metadata(self) -> None:
        """Test chunk metadata handling."""
        metadata = {"chunker": "TestChunker", "size": 100}
        chunk = Chunk(
            chunk_id="test_chunk",
            source_id="test_source",
            text="Test",
            chunk_index=0,
            start_char=0,
            end_char=4,
            metadata=metadata,
        )
        
        assert chunk.metadata == metadata


class TestSearchHit:
    """Test the SearchHit model."""
    
    def test_search_hit_creation(self, tmp_path) -> None:
        """Test creating a search hit."""
        chunk = Chunk(
            chunk_id="test_chunk",
            source_id="test_source",
            text="This is a relevant chunk.",
            chunk_index=0,
            start_char=0,
            end_char=25,
        )
        
        hit = SearchHit.from_chunk(
            chunk=chunk,
            similarity_score=0.85,
            rank=1,
            source_path=tmp_path / "test.txt",
        )
        
        assert hit.chunk == chunk
        assert hit.text == "This is a relevant chunk."
        assert hit.similarity_score == 0.85
        assert hit.rank == 1
        assert hit.source_path == tmp_path / "test.txt"
        assert hit.source_type == "txt"
        assert hit.is_high_similarity is True
        assert hit.is_medium_similarity is False
    
    def test_similarity_classification(self) -> None:
        """Test similarity score classification."""
        chunk = Chunk(
            chunk_id="test",
            source_id="test",
            text="Test",
            chunk_index=0,
            start_char=0,
            end_char=4,
        )
        
        # High similarity
        hit_high = SearchHit.from_chunk(
            chunk=chunk,
            similarity_score=0.9,
            rank=1,
            source_path=Path("test.txt"),
        )
        assert hit_high.is_high_similarity is True
        assert hit_high.is_medium_similarity is False
        
        # Medium similarity
        hit_medium = SearchHit.from_chunk(
            chunk=chunk,
            similarity_score=0.6,
            rank=1,
            source_path=Path("test.txt"),
        )
        assert hit_medium.is_high_similarity is False
        assert hit_medium.is_medium_similarity is True
        
        # Low similarity
        hit_low = SearchHit.from_chunk(
            chunk=chunk,
            similarity_score=0.3,
            rank=1,
            source_path=Path("test.txt"),
        )
        assert hit_low.is_high_similarity is False
        assert hit_low.is_medium_similarity is False
