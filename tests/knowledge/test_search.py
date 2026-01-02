"""
Tests for knowledge search functionality.

Tests the semantic search and retrieval functionality.
"""

from __future__ import annotations

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from ai_utilities.knowledge.search import KnowledgeSearch
from ai_utilities.knowledge.backend import SqliteVectorBackend
from ai_utilities.knowledge.models import Chunk
from ai_utilities.knowledge.exceptions import KnowledgeSearchError
from tests.knowledge.fake_embeddings import FakeEmbeddingProvider


class TestKnowledgeSearch:
    """Test the KnowledgeSearch class."""
    
    @pytest.fixture
    def temp_db(self) -> Path:
        """Create a temporary database file."""
        with TemporaryDirectory() as temp_dir:
            yield Path(temp_dir) / "test.db"
    
    @pytest.fixture
    def backend(self, temp_db) -> SqliteVectorBackend:
        """Create a backend instance with sample data."""
        backend = SqliteVectorBackend(
            db_path=temp_db,
            embedding_dimension=10,
            vector_extension="none",
        )
        
        # Create a test source first
        from ai_utilities.knowledge.models import Source
        from datetime import datetime
        
        source = Source(
            source_id="test_source",
            path="test.txt",
            file_size=165,
            mime_type="text/plain",
            mtime=1234567890,
            sha256_hash="abc123",
            indexed_at=datetime.utcnow(),
            chunk_count=3,
        )
        backend.upsert_source(source)
        
        # Insert sample chunks
        sample_chunks = [
            Chunk(
                chunk_id="chunk_0",
                source_id="test_source",
                text="This is about machine learning and artificial intelligence.",
                chunk_index=0,
                start_char=0,
                end_char=55,
                embedding=[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                embedding_model="test-model",
            ),
            Chunk(
                chunk_id="chunk_1", 
                source_id="test_source",
                text="Python programming is popular for data science applications.",
                chunk_index=1,
                start_char=55,
                end_char=110,
                embedding=[0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                embedding_model="test-model",
            ),
            Chunk(
                chunk_id="chunk_2",
                source_id="test_source",
                text="Deep learning models require large amounts of training data.",
                chunk_index=2,
                start_char=110,
                end_char=165,
                embedding=[0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                embedding_model="test-model",
            ),
        ]
        
        for chunk in sample_chunks:
            backend.upsert_chunk(chunk)
        
        return backend
    
    @pytest.fixture
    def search(self, backend) -> KnowledgeSearch:
        """Create a search instance."""
        embedding_client = FakeEmbeddingProvider(embedding_dimension=10)
        return KnowledgeSearch(
            backend=backend,
            embedding_client=embedding_client,
            embedding_model="test-model",
        )
    
    def test_search_initialization(self, search) -> None:
        """Test search initialization."""
        assert search.backend is not None
        assert search.embedding_client is not None
        assert search.embedding_model == "test-model"
    
    def test_basic_search(self, search) -> None:
        """Test basic semantic search."""
        # Query that should match first chunk about machine learning
        query = "machine learning algorithms"
        results = search.search(query, top_k=2)
        
        assert len(results) <= 2
        assert all(hasattr(result, 'chunk') for result in results)
        assert all(hasattr(result, 'similarity_score') for result in results)
        assert all(hasattr(result, 'rank') for result in results)
        
        # Results should be sorted by rank
        if len(results) > 1:
            assert results[0].rank == 1
            assert results[1].rank == 2
            assert results[0].similarity_score >= results[1].similarity_score
    
    def test_search_with_threshold(self, search) -> None:
        """Test search with similarity threshold."""
        # Very high threshold should return fewer results
        results = search.search("machine learning", top_k=5, similarity_threshold=0.9)
        assert len(results) <= 5
        
        # Low threshold should return more results
        results_low = search.search("machine learning", top_k=5, similarity_threshold=0.0)
        assert len(results_low) >= len(results)
    
    def test_search_empty_query(self, search) -> None:
        """Test search with empty query."""
        results = search.search("", top_k=5)
        assert results == []
        
        results = search.search("   ", top_k=5)
        assert results == []
    
    def test_search_top_k_limiting(self, search) -> None:
        """Test that top_k parameter limits results."""
        results_1 = search.search("machine learning", top_k=1)
        results_3 = search.search("machine learning", top_k=3)
        
        assert len(results_1) <= 1
        assert len(results_3) <= 3
        assert len(results_3) >= len(results_1)
    
    def test_search_metadata_inclusion(self, search) -> None:
        """Test search with and without metadata."""
        results_with_meta = search.search("machine learning", top_k=1, include_metadata=True)
        results_without_meta = search.search("machine learning", top_k=1, include_metadata=False)
        
        assert len(results_with_meta) == len(results_without_meta)
        
        if results_with_meta:
            # With metadata should have original metadata
            assert results_with_meta[0].chunk.metadata != {}
            
            # Without metadata should have empty metadata
            assert results_without_meta[0].chunk.metadata == {}
    
    def test_search_with_context(self, search) -> None:
        """Test search with context expansion."""
        results = search.search_with_context("machine learning", top_k=1, context_chars=50)
        
        assert len(results) <= 1
        
        if results:
            # Context should be longer than original chunk
            result = results[0]
            assert len(result.text) >= len(result.chunk.text)
    
    def test_find_similar_chunks(self, search) -> None:
        """Test finding chunks similar to a reference chunk."""
        # Find chunks similar to the first chunk
        results = search.find_similar_chunks("chunk_0", top_k=2)
        
        assert len(results) <= 2
        
        # Should not include the reference chunk itself
        chunk_ids = [result.chunk.chunk_id for result in results]
        assert "chunk_0" not in chunk_ids
        
        # Results should be sorted by similarity
        if len(results) > 1:
            assert results[0].similarity_score >= results[1].similarity_score
    
    def test_find_similar_nonexistent_chunk(self, search) -> None:
        """Test finding similar chunks for non-existent chunk."""
        with pytest.raises(KnowledgeSearchError):
            search.find_similar_chunks("nonexistent_chunk")
    
    def test_find_similar_chunk_no_embedding(self, backend) -> None:
        """Test finding similar chunks for chunk without embedding."""
        # Add chunk without embedding
        chunk_no_embedding = Chunk(
            chunk_id="chunk_no_embedding",
            source_id="test_source",
            text="This chunk has no embedding",
            chunk_index=3,
            start_char=165,
            end_char=195,
        )
        backend.upsert_chunk(chunk_no_embedding)
        
        embedding_client = FakeEmbeddingProvider(embedding_dimension=10)
        search = KnowledgeSearch(backend, embedding_client)
        
        with pytest.raises(KnowledgeSearchError):
            search.find_similar_chunks("chunk_no_embedding")
    
    def test_get_search_stats(self, search) -> None:
        """Test getting search statistics."""
        stats = search.get_search_stats()
        
        assert 'backend' in stats
        assert 'embedding' in stats
        assert 'search_capabilities' in stats
        
        assert stats['embedding']['model'] == "test-model"
        assert stats['embedding']['dimension'] == 10
        assert stats['search_capabilities']['semantic_search'] is True
        assert stats['search_capabilities']['context_search'] is True
        assert stats['search_capabilities']['similar_chunks'] is True
    
    def test_embedding_generation_error(self, backend) -> None:
        """Test handling of embedding generation errors."""
        # Create faulty embedding client
        class FaultyEmbeddingClient:
            def get_embeddings(self, texts, model=None):
                raise Exception("Embedding failed")
        
        search = KnowledgeSearch(backend, FaultyEmbeddingClient())
        
        with pytest.raises(KnowledgeSearchError):
            search.search("test query")
    
    def test_search_result_properties(self, search) -> None:
        """Test search hit computed properties."""
        results = search.search("machine learning", top_k=3)
        
        for result in results:
            # Test similarity classification
            if result.similarity_score > 0.8:
                assert result.is_high_similarity is True
            elif 0.5 <= result.similarity_score <= 0.8:
                assert result.is_medium_similarity is True
            else:
                assert result.is_high_similarity is False
                assert result.is_medium_similarity is False
    
    def test_search_source_path(self, search, temp_db) -> None:
        """Test that search results include correct source paths."""
        # Add a chunk with a known source path
        test_chunk = Chunk(
            chunk_id="test_chunk",
            source_id="/test/path/file.txt",
            text="Test content for path verification",
            chunk_index=0,
            start_char=0,
            end_char=40,
            embedding=[0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
            embedding_model="test-model",
        )
        
        # Manually insert the source for testing
        with search.backend._get_connection() as conn:
            conn.execute("""
                INSERT INTO sources (source_id, path, file_size, mime_type, mtime, sha256_hash, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "/test/path/file.txt",
                "/test/path/file.txt",
                40,
                "text/plain",
                1234567890.0,
                "testhash",
                1234567890.0,
            ))
            conn.commit()
        
        search.backend.upsert_chunk(test_chunk)
        
        results = search.search("test content", top_k=1)
        
        if results:
            assert results[0].source_path == Path("/test/path/file.txt")
            assert results[0].source_type == "txt"
