"""
Tests for SQLite vector backend.

Tests the vector storage and similarity search functionality.
"""

from __future__ import annotations

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from ai_utilities.knowledge.backend import SqliteVectorBackend
from ai_utilities.knowledge.models import Chunk
from ai_utilities.knowledge.exceptions import SqliteExtensionUnavailableError
from tests.knowledge.fake_embeddings import FakeEmbeddingProvider


class TestSqliteVectorBackend:
    """Test the SqliteVectorBackend class."""
    
    @pytest.fixture
    def temp_db(self) -> Path:
        """Create a temporary database file."""
        with TemporaryDirectory() as temp_dir:
            yield Path(temp_dir) / "test.db"
    
    @pytest.fixture
    def backend(self, temp_db) -> SqliteVectorBackend:
        """Create a backend instance for testing."""
        backend = SqliteVectorBackend(
            db_path=temp_db,
            embedding_dimension=10,
            vector_extension="none",  # Don't use extensions for testing
        )
        
        # Create a test source for foreign key constraints
        from ai_utilities.knowledge.models import Source
        from datetime import datetime
        
        source = Source(
            source_id="test_source",
            path="test.txt",
            file_size=100,
            mime_type="text/plain",
            mtime=1234567890,
            sha256_hash="abc123",
            indexed_at=datetime.utcnow(),
            chunk_count=0,
        )
        backend.upsert_source(source)
        
        return backend
    
    @pytest.fixture
    def sample_chunks(self) -> list[Chunk]:
        """Create sample chunks for testing."""
        chunks = []
        for i in range(3):
            chunk = Chunk(
                chunk_id=f"chunk_{i}",
                source_id="test_source",
                text=f"This is test chunk number {i}.",
                chunk_index=i,
                start_char=i * 30,
                end_char=(i + 1) * 30,
                embedding=[float(j + i) for j in range(10)],  # Simple deterministic embeddings
                embedding_model="test-model",
            )
            chunks.append(chunk)
        return chunks
    
    def test_backend_initialization(self, temp_db) -> None:
        """Test backend initialization."""
        backend = SqliteVectorBackend(
            db_path=temp_db,
            embedding_dimension=5,
            vector_extension="none",
        )
        
        assert backend.db_path == temp_db
        assert backend.embedding_dimension == 5
        assert backend.vector_extension == "none"
        assert backend._extension_available is False
        
        # Check that database file was created
        assert temp_db.exists()
        
        # Check stats
        stats = backend.get_stats()
        assert stats['sources_count'] == 0
        assert stats['chunks_count'] == 0
        assert stats['embeddings_count'] == 0
        assert stats['extension_available'] is False
    
    def test_extension_not_available(self, temp_db) -> None:
        """Test behavior when SQLite extension is not available."""
        backend = SqliteVectorBackend(
            db_path=temp_db,
            embedding_dimension=5,
            vector_extension="auto",  # Try auto mode (should fallback)
        )
        
        # Should fallback to regular storage when extension not available
        assert backend._extension_available is False
        assert backend._fallback_reason is not None
        assert "none of the tried extensions" in backend._fallback_reason
    
    def test_required_extension_fails(self, temp_db) -> None:
        """Test that required extensions fail fast when not available."""
        from ai_utilities.knowledge.exceptions import SqliteExtensionUnavailableError
        
        # Should raise exception when required extension is not available
        with pytest.raises(SqliteExtensionUnavailableError) as exc_info:
            SqliteVectorBackend(
                db_path=temp_db,
                embedding_dimension=5,
                vector_extension="sqlite-vec",  # Required extension
            )
        
        # Verify the error message is helpful
        assert "could not be loaded" in str(exc_info.value)
        assert "vec" in str(exc_info.value)  # Internal extension name
    
    def test_upsert_and_get_chunk(self, backend, sample_chunks) -> None:
        """Test upserting and retrieving chunks."""
        chunk = sample_chunks[0]
        
        # Upsert chunk
        backend.upsert_chunk(chunk)
        
        # Retrieve chunk
        retrieved = backend.get_chunk(chunk.chunk_id)
        assert retrieved is not None
        assert retrieved.chunk_id == chunk.chunk_id
        assert retrieved.source_id == chunk.source_id
        assert retrieved.text == chunk.text
        assert retrieved.embedding == chunk.embedding
        assert retrieved.embedding_model == chunk.embedding_model
    
    def test_get_nonexistent_chunk(self, backend) -> None:
        """Test retrieving a non-existent chunk."""
        retrieved = backend.get_chunk("nonexistent")
        assert retrieved is None
    
    def test_update_chunk(self, backend, sample_chunks) -> None:
        """Test updating an existing chunk."""
        chunk = sample_chunks[0]
        
        # Insert original chunk
        backend.upsert_chunk(chunk)
        
        # Update chunk with different text
        updated_chunk = Chunk(
            chunk_id=chunk.chunk_id,
            source_id=chunk.source_id,
            text="Updated text content",
            chunk_index=chunk.chunk_index,
            start_char=chunk.start_char,
            end_char=chunk.end_char,
            embedding=[float(j + 10) for j in range(10)],  # Different embedding
            embedding_model="updated-model",
        )
        
        backend.upsert_chunk(updated_chunk)
        
        # Retrieve updated chunk
        retrieved = backend.get_chunk(chunk.chunk_id)
        assert retrieved is not None
        assert retrieved.text == "Updated text content"
        assert retrieved.embedding_model == "updated-model"
        assert retrieved.embedding != chunk.embedding
    
    def test_source_operations(self, backend, sample_chunks) -> None:
        """Test source-related operations."""
        # Insert chunks
        for chunk in sample_chunks:
            backend.upsert_chunk(chunk)
        
        # Get source chunks
        source_chunks = backend.get_source_chunks("test_source")
        assert len(source_chunks) == len(sample_chunks)
        
        # Check that chunks are in correct order
        for i, chunk in enumerate(source_chunks):
            assert chunk.chunk_index == i
            assert chunk.source_id == "test_source"
    
    def test_delete_source(self, backend, sample_chunks) -> None:
        """Test deleting a source and its chunks."""
        # Insert chunks
        for chunk in sample_chunks:
            backend.upsert_chunk(chunk)
        
        # Verify chunks exist
        retrieved = backend.get_chunk("chunk_0")
        assert retrieved is not None
        
        # Delete source
        backend.delete_source("test_source")
        
        # Verify chunks are deleted
        retrieved = backend.get_chunk("chunk_0")
        assert retrieved is None
        
        source_chunks = backend.get_source_chunks("test_source")
        assert len(source_chunks) == 0
    
    def test_similarity_search(self, backend, sample_chunks) -> None:
        """Test similarity search functionality."""
        # Insert chunks
        for chunk in sample_chunks:
            backend.upsert_chunk(chunk)
        
        # Search with query embedding similar to first chunk
        query_embedding = [float(j) for j in range(10)]  # Similar to chunk_0
        results = backend.search_similar(query_embedding, top_k=2)
        
        assert len(results) <= 2
        assert all(isinstance(result, tuple) and len(result) == 2 for result in results)
        assert all(isinstance(chunk_id, str) and isinstance(score, float) for chunk_id, score in results)
        
        # Results should be sorted by similarity (higher is better)
        if len(results) > 1:
            assert results[0][1] >= results[1][1]
    
    def test_similarity_search_with_threshold(self, backend, sample_chunks) -> None:
        """Test similarity search with threshold."""
        # Insert chunks
        for chunk in sample_chunks:
            backend.upsert_chunk(chunk)
        
        # Search with high threshold
        query_embedding = [float(j) for j in range(10)]
        results = backend.search_similar(query_embedding, top_k=5, similarity_threshold=0.9)
        
        # Should return fewer or no results with high threshold
        assert len(results) <= 5
    
    def test_search_empty_database(self, backend) -> None:
        """Test search on empty database."""
        query_embedding = [float(j) for j in range(10)]
        results = backend.search_similar(query_embedding)
        
        assert results == []
    
    def test_stats(self, backend, sample_chunks) -> None:
        """Test database statistics."""
        # Initial stats (test source created by fixture)
        stats = backend.get_stats()
        assert stats['sources_count'] == 1
        assert stats['chunks_count'] == 0
        assert stats['embeddings_count'] == 0
        
        # Insert chunks
        for chunk in sample_chunks:
            backend.upsert_chunk(chunk)
        
        # Updated stats
        stats = backend.get_stats()
        assert stats['chunks_count'] == len(sample_chunks)
        assert stats['embeddings_count'] == len(sample_chunks)
        assert stats['db_size_bytes'] > 0
    
    def test_existing_sources(self, backend, sample_chunks) -> None:
        """Test getting existing source IDs."""
        existing = backend.get_existing_sources()
        # Test source created by fixture
        assert existing == ['test_source']
        
        # Insert chunks
        for chunk in sample_chunks:
            backend.upsert_chunk(chunk)
        
        existing = backend.get_existing_sources()
        assert "test_source" in existing
    
    def test_source_hash_tracking(self, backend, sample_chunks) -> None:
        """Test source hash tracking for change detection."""
        # Test source has hash from fixture
        hash_value = backend.get_source_hash("test_source")
        assert hash_value == "abc123"  # Set in fixture
        
        # Insert chunk (this doesn't change source hash)
        backend.upsert_chunk(sample_chunks[0])
        
        # Hash remains the same
        hash_value = backend.get_source_hash("test_source")
        assert hash_value == "abc123"
    
    def test_close_connection(self, backend) -> None:
        """Test closing database connections."""
        # Should not raise any errors
        backend.close()
        
        # Can still use after close (creates new connection)
        chunk = Chunk(
            chunk_id="test_chunk",
            source_id="test_source",
            text="Test",
            chunk_index=0,
            start_char=0,
            end_char=4,
        )
        backend.upsert_chunk(chunk)
        
        retrieved = backend.get_chunk("test_chunk")
        assert retrieved is not None
