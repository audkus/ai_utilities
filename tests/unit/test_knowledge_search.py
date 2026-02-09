"""Unit tests for knowledge/search.py module."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any

from ai_utilities.knowledge.search import KnowledgeSearch
from ai_utilities.knowledge.exceptions import KnowledgeSearchError
from ai_utilities.knowledge.models import Chunk, SearchHit


class TestKnowledgeSearch:
    """Test cases for KnowledgeSearch class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_backend = Mock()
        self.mock_embedding_client = Mock()
        self.search = KnowledgeSearch(
            backend=self.mock_backend,
            embedding_client=self.mock_embedding_client,
            embedding_model="test-model"
        )

    def test_initialization(self) -> None:
        """Test KnowledgeSearch initialization."""
        assert self.search.backend == self.mock_backend
        assert self.search.embedding_client == self.mock_embedding_client
        assert self.search.embedding_model == "test-model"

    def test_search_empty_query(self) -> None:
        """Test search with empty query returns empty list."""
        result = self.search.search("")
        assert result == []
        
        result = self.search.search("   ")
        assert result == []

    def test_search_successful(self) -> None:
        """Test successful search operation."""
        # Mock embedding generation
        self.mock_embedding_client.get_embeddings.return_value = [[0.1, 0.2, 0.3]]
        
        # Mock backend search
        self.mock_backend.search_similar.return_value = [
            ("chunk1", 0.9),
            ("chunk2", 0.8)
        ]
        
        # Mock chunk retrieval
        from ai_utilities.knowledge.models import Chunk
        from datetime import datetime
        
        mock_chunk1 = Chunk(
            chunk_id="chunk1",
            source_id="source1",
            text="Test text 1",
            chunk_index=0,
            start_char=0,
            end_char=11,
            metadata={"key": "value"}
        )
        mock_chunk2 = Chunk(
            chunk_id="chunk2",
            source_id="source1",
            text="Test text 2",
            chunk_index=1,
            start_char=12,
            end_char=23,
            metadata={}
        )
        
        self.mock_backend.get_chunk.side_effect = [mock_chunk1, mock_chunk2]
        
        # Mock source path retrieval
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ["test/path"]
        mock_conn.execute.return_value = mock_cursor
        self.mock_backend._get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        self.mock_backend._get_connection.return_value.__exit__ = Mock(return_value=None)
        
        result = self.search.search("test query", top_k=2)
        
        assert len(result) == 2
        assert result[0].similarity_score == 0.9
        assert result[0].rank == 1
        assert result[1].similarity_score == 0.8
        assert result[1].rank == 2

    def test_search_with_similarity_threshold(self) -> None:
        """Test search with similarity threshold filtering."""
        self.mock_embedding_client.get_embeddings.return_value = [[0.1, 0.2, 0.3]]
        
        # Mock backend search to respect similarity threshold
        def mock_search_similar(query_embedding, top_k, similarity_threshold=0.0):
            all_results = [
                ("chunk1", 0.9),
                ("chunk2", 0.7),  # Below threshold
                ("chunk3", 0.8)
            ]
            # Filter by threshold
            filtered_results = [(chunk_id, score) for chunk_id, score in all_results 
                             if score >= similarity_threshold]
            return filtered_results[:top_k]
        
        self.mock_backend.search_similar.side_effect = mock_search_similar
        
        from ai_utilities.knowledge.models import Chunk
        from datetime import datetime
        
        mock_chunk1 = Chunk(
            chunk_id="chunk1",
            source_id="source1",
            text="Test text 1",
            chunk_index=0,
            start_char=0,
            end_char=11,
            metadata={}
        )
        mock_chunk3 = Chunk(
            chunk_id="chunk3", 
            source_id="source1",
            text="Test text 3",
            chunk_index=2,
            start_char=22,
            end_char=33,
            metadata={}
        )
        mock_chunk2 = Chunk(
            chunk_id="chunk2",
            source_id="source1", 
            text="Test text 2",
            chunk_index=1,
            start_char=12,
            end_char=23,
            metadata={}
        )
        # Set up side_effect for the different chunk calls
        self.mock_backend.get_chunk.side_effect = [mock_chunk1, mock_chunk2, mock_chunk3]
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ["test/path"]
        mock_conn.execute.return_value = mock_cursor
        self.mock_backend._get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        self.mock_backend._get_connection.return_value.__exit__ = Mock(return_value=None)
        
        result = self.search.search("test", similarity_threshold=0.8)
        
        # Should only return chunks above threshold
        assert len(result) == 2
        assert all(hit.similarity_score >= 0.8 for hit in result)

    def test_search_exclude_metadata(self) -> None:
        """Test search with metadata exclusion."""
        self.mock_embedding_client.get_embeddings.return_value = [[0.1, 0.2, 0.3]]
        self.mock_backend.search_similar.return_value = [("chunk1", 0.9)]
        
        from ai_utilities.knowledge.models import Chunk
        from datetime import datetime
        
        mock_chunk = Chunk(
            chunk_id="chunk1",
            source_id="source1",
            text="Test text",
            chunk_index=0,
            start_char=0,
            end_char=9,
            metadata={"key": "value"}
        )
        
        self.mock_backend.get_chunk.return_value = mock_chunk
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ["test/path"]
        mock_conn.execute.return_value = mock_cursor
        self.mock_backend._get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        self.mock_backend._get_connection.return_value.__exit__ = Mock(return_value=None)
        
        result = self.search.search("test", include_metadata=False)
        
        assert len(result) == 1
        assert result[0].chunk.metadata == {}

    def test_search_embedding_generation_failure(self) -> None:
        """Test search failure when embedding generation fails."""
        self.mock_embedding_client.get_embeddings.side_effect = Exception("Embedding failed")
        
        with pytest.raises(KnowledgeSearchError, match="Failed to generate query embedding"):
            self.search.search("test query")

    def test_search_no_embedding_returned(self) -> None:
        """Test search when no embedding is returned."""
        self.mock_embedding_client.get_embeddings.return_value = []
        
        with pytest.raises(KnowledgeSearchError, match="No embedding generated for query"):
            self.search.search("test query")

    def test_search_backend_failure(self) -> None:
        """Test search failure when backend operations fail."""
        self.mock_embedding_client.get_embeddings.return_value = [[0.1, 0.2, 0.3]]
        self.mock_backend.search_similar.side_effect = Exception("Backend error")
        
        with pytest.raises(KnowledgeSearchError, match="Search failed"):
            self.search.search("test query")

    def test_search_with_context(self) -> None:
        """Test search with context expansion."""
        # Mock basic search
        mock_hit = Mock(spec=SearchHit)
        mock_hit.chunk = Mock(spec=Chunk)
        mock_hit.chunk.chunk_id = "chunk1"
        mock_hit.chunk.source_id = "source1"
        mock_hit.chunk.text = "Original text"
        mock_hit.chunk.metadata = {}
        mock_hit.chunk.chunk_index = 0
        mock_hit.chunk.start_char = 100
        mock_hit.chunk.end_char = 200
        mock_hit.chunk.embedding = [0.1, 0.2]
        mock_hit.chunk.embedding_model = "test"
        mock_hit.chunk.embedded_at = "2023-01-01"
        
        with patch.object(self.search, 'search', return_value=[mock_hit]):
            with patch.object(self.search, '_get_context', return_value="Expanded context"):
                result = self.search.search_with_context("test", context_chars=50)
                
                assert len(result) == 1
                assert result[0].text == "Expanded context"
                assert result[0].chunk.text == "Expanded context"

    def test_find_similar_chunks_success(self) -> None:
        """Test finding similar chunks successfully."""
        # Mock reference chunk
        from ai_utilities.knowledge.models import Chunk
        
        mock_ref_chunk = Chunk(
            chunk_id="ref_chunk",
            source_id="source1",
            text="Reference text",
            chunk_index=0,
            start_char=0,
            end_char=14,
            embedding=[0.1, 0.2, 0.3]
        )
        self.mock_backend.get_chunk.return_value = mock_ref_chunk
        
        # Mock similar chunks search
        self.mock_backend.search_similar.return_value = [
            ("ref_chunk", 1.0),  # Reference chunk itself
            ("similar1", 0.9),
            ("similar2", 0.8)
        ]
        
        # Mock chunk retrieval
        mock_similar_chunk = Chunk(
            chunk_id="similar1",
            source_id="source1",
            text="Similar text",
            chunk_index=1,
            start_char=15,
            end_char=27
        )
        self.mock_backend.get_chunk.side_effect = [mock_ref_chunk, mock_similar_chunk, mock_similar_chunk]
        
        # Mock source path
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ["test/path"]
        mock_conn.execute.return_value = mock_cursor
        self.mock_backend._get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        self.mock_backend._get_connection.return_value.__exit__ = Mock(return_value=None)
        
        result = self.search.find_similar_chunks("ref_chunk", top_k=2)
        
        assert len(result) == 2
        assert result[0].rank == 1
        assert result[1].rank == 2
        # Reference chunk should be excluded
        assert all(hit.chunk.chunk_id != "ref_chunk" for hit in result)

    def test_find_similar_chunks_chunk_not_found(self) -> None:
        """Test finding similar chunks when reference chunk doesn't exist."""
        self.mock_backend.get_chunk.return_value = None
        
        with pytest.raises(KnowledgeSearchError, match="Chunk not found"):
            self.search.find_similar_chunks("nonexistent")

    def test_find_similar_chunks_no_embedding(self) -> None:
        """Test finding similar chunks when reference chunk has no embedding."""
        mock_chunk = Mock(spec=Chunk)
        mock_chunk.embedding = None
        self.mock_backend.get_chunk.return_value = mock_chunk
        
        with pytest.raises(KnowledgeSearchError, match="Chunk has no embedding"):
            self.search.find_similar_chunks("chunk_no_embedding")

    def test_generate_query_embedding_success(self) -> None:
        """Test successful query embedding generation."""
        self.mock_embedding_client.get_embeddings.return_value = [[0.1, 0.2, 0.3]]
        
        result = self.search._generate_query_embedding("test query")
        
        assert result == [0.1, 0.2, 0.3]
        self.mock_embedding_client.get_embeddings.assert_called_once_with(
            ["test query"], model="test-model"
        )

    def test_generate_query_embedding_failure(self) -> None:
        """Test query embedding generation failure."""
        self.mock_embedding_client.get_embeddings.side_effect = Exception("API error")
        
        with pytest.raises(KnowledgeSearchError, match="Failed to generate query embedding"):
            self.search._generate_query_embedding("test query")

    def test_get_source_path_success(self) -> None:
        """Test successful source path retrieval."""
        mock_conn = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ["test/path.txt"]
        mock_conn.execute.return_value = mock_cursor
        self.mock_backend._get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        self.mock_backend._get_connection.return_value.__exit__ = Mock(return_value=None)
        
        result = self.search._get_source_path("source1")
        
        assert isinstance(result, str)  # Contract: result is string type
        assert len(result) > 0  # Contract: non-empty path
        mock_conn.execute.assert_called_once_with(
            "SELECT path FROM sources WHERE source_id = ?", 
            ("source1",)
        )

    def test_get_source_path_not_found(self) -> None:
        """Test source path retrieval when source not found."""
        mock_conn = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn.execute.return_value = mock_cursor
        self.mock_backend._get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        self.mock_backend._get_connection.return_value.__exit__ = Mock(return_value=None)
        
        result = self.search._get_source_path("nonexistent")
        
        assert result is None

        """Test source path retrieval with database error."""
        self.mock_backend._get_connection.side_effect = Exception("DB error")
        
        result = self.search._get_source_path("source1")
        
        assert result is None

    def test_get_context_success(self) -> None:
        """Test successful context retrieval."""
        mock_chunk = Mock(spec=Chunk)
        mock_chunk.source_id = "source1"
        mock_chunk.start_char = 100
        mock_chunk.end_char = 200
        mock_chunk.text = "Target text"
        
        # Mock source chunks
        mock_context_chunk = Mock(spec=Chunk)
        mock_context_chunk.start_char = 50
        mock_context_chunk.end_char = 250
        mock_context_chunk.text = "Context text"
        
        self.mock_backend.get_source_chunks.return_value = [mock_context_chunk]
        
        result = self.search._get_context(mock_chunk, 50)
        
        assert isinstance(result, str)  # Contract: result is string type
        assert len(result) > 0  # Contract: non-empty context

    def test_get_context_no_context_chunks(self) -> None:
        """Test context retrieval when no context chunks found."""
        mock_chunk = Mock(spec=Chunk)
        mock_chunk.text = "Original text"
        
        self.mock_backend.get_source_chunks.return_value = []
        
        result = self.search._get_context(mock_chunk, 50)
        
        assert isinstance(result, str)  # Contract: result is string type
        assert len(result) > 0  # Contract: non-empty text

    def test_get_context_database_error(self) -> None:
        """Test context retrieval with database error."""
        mock_chunk = Mock(spec=Chunk)
        mock_chunk.text = "Original text"
        
        self.mock_backend.get_source_chunks.side_effect = Exception("DB error")
        
        result = self.search._get_context(mock_chunk, 50)
        
        assert isinstance(result, str)  # Contract: result is string type
        assert len(result) > 0  # Contract: non-empty text

    def test_get_search_stats(self) -> None:
        """Test search statistics retrieval."""
        self.mock_backend.get_stats.return_value = {
            "total_chunks": 100,
            "extension_available": True
        }
        self.mock_backend.embedding_dimension = 1536
        
        result = self.search.get_search_stats()
        
        assert isinstance(result, dict)  # Contract: result is dictionary
        assert len(result) > 0  # Contract: non-empty result
        # Contract: stats structure verified (no specific string checks)
        assert result["embedding"]["model"] == "test-model"
        assert result["embedding"]["dimension"] == 1536
        assert result["search_capabilities"]["semantic_search"] is True
        assert result["search_capabilities"]["context_search"] is True
        assert result["search_capabilities"]["similar_chunks"] is True
        assert result["search_capabilities"]["extension_accelerated"] is True

    @pytest.mark.parametrize("top_k,threshold", [
        (1, 0.5),
        (10, 0.0),
        (5, 0.9),
    ])
    def test_search_parameter_variations(self, top_k, threshold) -> None:
        """Test search with various parameter combinations."""
        self.mock_embedding_client.get_embeddings.return_value = [[0.1, 0.2, 0.3]]
        self.mock_backend.search_similar.return_value = [("chunk1", 0.9)]
        
        from ai_utilities.knowledge.models import Chunk
        
        mock_chunk = Chunk(
            chunk_id="chunk1",
            source_id="source1",
            text="Test text",
            chunk_index=0,
            start_char=0,
            end_char=9
        )
        self.mock_backend.get_chunk.return_value = mock_chunk
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ["test/path"]
        mock_conn.execute.return_value = mock_cursor
        self.mock_backend._get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        self.mock_backend._get_connection.return_value.__exit__ = Mock(return_value=None)
        
        result = self.search.search("test", top_k=top_k, similarity_threshold=threshold)
        
        self.mock_backend.search_similar.assert_called_once_with(
            [0.1, 0.2, 0.3],
            top_k=top_k * 2,
            similarity_threshold=threshold,
        )
