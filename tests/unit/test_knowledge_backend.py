"""Unit tests for knowledge/backend.py module."""

import pytest
import sqlite3
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from ai_utilities.knowledge.backend import SqliteVectorBackend
from ai_utilities.knowledge.exceptions import SqliteExtensionUnavailableError


class TestSqliteVectorBackend:
    """Test cases for SqliteVectorBackend class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.db_path = Path("/tmp/test_db.sqlite")
        self.embedding_dim = 1536
        
    def test_initialization_auto_extension(self) -> None:
        """Test backend initialization with auto extension detection."""
        with patch('sqlite3.connect'), \
             patch.object(SqliteVectorBackend, '_init_database') as mock_init:
            
            backend = SqliteVectorBackend(
                db_path=self.db_path,
                embedding_dimension=self.embedding_dim,
                vector_extension="auto"
            )
            
            assert backend.db_path == self.db_path
            assert backend.embedding_dimension == self.embedding_dim
            assert backend.vector_extension == "auto"
            mock_init.assert_called_once()

    def test_initialization_specific_extension(self) -> None:
        """Test backend initialization with specific extension."""
        with patch('sqlite3.connect'), \
             patch.object(SqliteVectorBackend, '_init_database'):
            
            backend = SqliteVectorBackend(
                db_path=self.db_path,
                embedding_dimension=self.embedding_dim,
                vector_extension="sqlite-vec"
            )
            
            assert backend.vector_extension == "sqlite-vec"

    def test_initialization_none_extension(self) -> None:
        """Test backend initialization with no extension (fallback mode)."""
        with patch('sqlite3.connect'), \
             patch.object(SqliteVectorBackend, '_init_database'):
            
            backend = SqliteVectorBackend(
                db_path=self.db_path,
                embedding_dimension=self.embedding_dim,
                vector_extension="none"
            )
            
            assert backend.vector_extension == "none"

    def test_get_connection_thread_local(self) -> None:
        """Test that connections are thread-local."""
        with patch('sqlite3.connect') as mock_connect, \
             patch.object(SqliteVectorBackend, '_init_database'):
            
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            
            backend = SqliteVectorBackend(
                db_path=self.db_path,
                embedding_dimension=self.embedding_dim
            )
            
            # First connection
            with backend._get_connection() as conn1:
                assert conn1 == mock_conn
                mock_connect.assert_called_once()
            
            # Second connection in same thread should reuse
            with backend._get_connection() as conn2:
                assert conn2 == mock_conn
                mock_connect.assert_called_once()  # Still only called once

    def test_get_connection_exception_handling(self) -> None:
        """Test connection exception handling."""
        with patch('sqlite3.connect') as mock_connect, \
             patch.object(SqliteVectorBackend, '_init_database'):
            
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            
            backend = SqliteVectorBackend(
                db_path=self.db_path,
                embedding_dimension=self.embedding_dim
            )
            
            # Test exception handling
            with pytest.raises(ValueError):
                with backend._get_connection() as conn:
                    conn.execute("SELECT 1")
                    raise ValueError("Test error")
            
            # Rollback should be called
            mock_conn.rollback.assert_called_once()

    def test_connection_pragmas(self) -> None:
        """Test that connection pragmas are set correctly."""
        with patch('sqlite3.connect') as mock_connect, \
             patch.object(SqliteVectorBackend, '_init_database'):
            
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            
            backend = SqliteVectorBackend(
                db_path=self.db_path,
                embedding_dimension=self.embedding_dim
            )
            
            # Trigger connection creation
            with backend._get_connection():
                pass
            
            # Check that pragmas were set
            expected_calls = [
                ("PRAGMA foreign_keys = ON",),
                ("PRAGMA journal_mode = WAL",),
                ("PRAGMA synchronous = NORMAL",),
                ("PRAGMA cache_size=10000",),
                ("PRAGMA temp_store=memory",),
            ]
            
            actual_calls = [call[0] for call in mock_conn.execute.call_args_list]
            for expected_call in expected_calls:
                assert expected_call in actual_calls

    def test_init_database_schema_creation(self) -> None:
        """Test database schema initialization."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            
            backend = SqliteVectorBackend(
                db_path=self.db_path,
                embedding_dimension=self.embedding_dim
            )
            
            # Check that sources table was created
            sources_calls = [call for call in mock_conn.execute.call_args_list 
                           if "sources" in str(call)]
            assert len(sources_calls) > 0
            
            # Check that chunks table was created
            chunks_calls = [call for call in mock_conn.execute.call_args_list 
                          if "chunks" in str(call)]
            assert len(chunks_calls) > 0

    def test_add_source(self) -> None:
        """Test adding a source to the database."""
        with patch('sqlite3.connect') as mock_connect, \
             patch.object(SqliteVectorBackend, '_init_database'):
            
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            
            backend = SqliteVectorBackend(
                db_path=self.db_path,
                embedding_dimension=self.embedding_dim
            )
            
            from ai_utilities.knowledge.models import Source
            from datetime import datetime
            from pathlib import Path
            
            source = Source(
                source_id="test_source",
                path=Path("/path/to/source"),
                file_size=1024,
                mime_type="text/plain",
                mtime=datetime.now(),
                sha256_hash="abc123",
                chunk_count=5
            )
            
            backend.upsert_source(source)
            
            # Verify the insert was called
            insert_calls = [call for call in mock_conn.execute.call_args_list 
                          if "INSERT OR REPLACE" in str(call)]
            assert len(insert_calls) == 1

    def test_get_source(self) -> None:
        """Test retrieving a source from the database."""
        with patch('sqlite3.connect') as mock_connect, \
             patch.object(SqliteVectorBackend, '_init_database'):
            
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.execute.return_value = mock_cursor
            mock_cursor.fetchone.return_value = (
                "test_source", "/test/path", 1024, "text/plain", "text", 
                "abc123", 1234567890.0, "hash123", 1234567891.0, 5
            )
            mock_connect.return_value = mock_conn
            
            backend = SqliteVectorBackend(
                db_path=self.db_path,
                embedding_dimension=self.embedding_dim
            )
            
            source = backend.get_source("test_source")
            
            assert source is not None
            assert source.source_id == "test_source"
            assert str(source.path) == "/test/path"
            assert source.file_size == 1024

    def test_get_source_not_found(self) -> None:
        """Test retrieving a non-existent source."""
        with patch('sqlite3.connect') as mock_connect, \
             patch.object(SqliteVectorBackend, '_init_database'):
            
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.execute.return_value = mock_cursor
            mock_cursor.fetchone.return_value = None
            mock_connect.return_value = mock_conn
            
            backend = SqliteVectorBackend(
                db_path=self.db_path,
                embedding_dimension=self.embedding_dim
            )
            
            source = backend.get_source("nonexistent")
            assert source is None

    def test_upsert_chunk(self) -> None:
        """Test upserting a chunk to the database."""
        with patch('sqlite3.connect') as mock_connect, \
             patch.object(SqliteVectorBackend, '_init_database'):
            
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            
            backend = SqliteVectorBackend(
                db_path=self.db_path,
                embedding_dimension=self.embedding_dim
            )
            
            from ai_utilities.knowledge.models import Chunk
            from datetime import datetime
            
            chunk = Chunk(
                chunk_id="test_chunk",
                source_id="test_source",
                text="Test content",
                chunk_index=0,
                start_char=0,
                end_char=12,
                embedding=[0.1] * self.embedding_dim,  # Match embedding dimension
                embedded_at=datetime.now()
            )
            
            backend.upsert_chunk(chunk)
            
            # Verify the insert was called - look for chunks table insert
            insert_calls = [call for call in mock_conn.execute.call_args_list 
                          if "INSERT OR REPLACE INTO chunks" in str(call)]
            assert len(insert_calls) == 1

    def test_get_chunk(self) -> None:
        """Test retrieving a chunk from the database."""
        with patch('sqlite3.connect') as mock_connect, \
             patch.object(SqliteVectorBackend, '_init_database'):
            
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.execute.return_value = mock_cursor
            mock_cursor.fetchone.return_value = (
                "test_chunk", "test_source", "Test chunk content", 
                '{"key": "value"}', 0, 0, 20, b'\x00\x01\x02', 
                1672531200, 1536, b'\x00\x01\x02\x03'
            )
            mock_connect.return_value = mock_conn
            
            backend = SqliteVectorBackend(
                db_path=self.db_path,
                embedding_dimension=self.embedding_dim
            )
            
            chunk = backend.get_chunk("test_chunk")
            
            assert chunk is not None
            assert chunk.chunk_id == "test_chunk"
            assert chunk.source_id == "test_source"
            assert isinstance(chunk.text, str)  # Contract: text is string type
            assert len(chunk.text) > 0  # Contract: non-empty text

    def test_get_chunk_not_found(self) -> None:
        """Test retrieving a non-existent chunk."""
        with patch('sqlite3.connect') as mock_connect, \
             patch.object(SqliteVectorBackend, '_init_database'):
            
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.execute.return_value = mock_cursor
            mock_cursor.fetchone.return_value = None
            mock_connect.return_value = mock_conn
            
            backend = SqliteVectorBackend(
                db_path=self.db_path,
                embedding_dimension=self.embedding_dim
            )
            
            chunk = backend.get_chunk("nonexistent")
            assert chunk is None

    def test_get_source_chunks(self) -> None:
        """Test retrieving all chunks for a source."""
        with patch('sqlite3.connect') as mock_connect, \
             patch.object(SqliteVectorBackend, '_init_database'):
            
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.execute.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [
                ("chunk1", "source1", "Text 1", '{}', 0, 0, 10, b'\x00\x01', 1672531200, 1536),
                ("chunk2", "source1", "Text 2", '{}', 1, 11, 20, b'\x01\x02', 1672531200, 1536)
            ]
            mock_connect.return_value = mock_conn
            
            backend = SqliteVectorBackend(
                db_path=self.db_path,
                embedding_dimension=self.embedding_dim
            )
            
            chunks = backend.get_source_chunks("source1")
            
            assert len(chunks) == 2
            assert chunks[0].chunk_id == "chunk1"
            assert chunks[1].chunk_id == "chunk2"

    def test_search_similar_fallback_mode(self) -> None:
        """Test similarity search in fallback mode (no extensions)."""
        with patch('sqlite3.connect') as mock_connect, \
             patch.object(SqliteVectorBackend, '_init_database'):
            
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.execute.return_value = mock_cursor
            # Return empty results for fallback mode
            mock_cursor.fetchall.return_value = []
            mock_connect.return_value = mock_conn
            
            backend = SqliteVectorBackend(
                db_path=self.db_path,
                embedding_dimension=3,  # Match test embedding
                vector_extension="none"
            )
            
            query_embedding = [0.1, 0.2, 0.3]
            results = backend.search_similar(query_embedding, top_k=5)
            
            assert isinstance(results, list)
            # In fallback mode, should return empty list or basic results

    def test_get_stats(self) -> None:
        """Test getting database statistics."""
        with patch('sqlite3.connect') as mock_connect, \
             patch.object(SqliteVectorBackend, '_init_database'):
            
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.execute.return_value = mock_cursor
            mock_cursor.fetchone.side_effect = [
                (10,),  # Source count
                (100,),  # Chunk count
                (1536,),  # Embedding dimension
                (0,)  # Extension available
            ]
            mock_connect.return_value = mock_conn
            
            backend = SqliteVectorBackend(
                db_path=self.db_path,
                embedding_dimension=self.embedding_dim
            )
            
            stats = backend.get_stats()
            
            assert "sources_count" in stats
            assert "chunks_count" in stats
            assert "embeddings_count" in stats
            assert "extension_available" in stats
            assert stats["sources_count"] == 10
            assert stats["chunks_count"] == 100
            assert stats["embeddings_count"] == 1536
            assert stats["extension_available"] is False

    def test_delete_source(self) -> None:
        """Test deleting a source and its chunks."""
        with patch('sqlite3.connect') as mock_connect, \
             patch.object(SqliteVectorBackend, '_init_database'):
            
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            
            backend = SqliteVectorBackend(
                db_path=self.db_path,
                embedding_dimension=self.embedding_dim
            )
            
            backend.delete_source("test_source")
            
            # Verify both chunks and source were deleted
            delete_calls = [call for call in mock_conn.execute.call_args_list 
                           if "DELETE" in str(call)]
            assert len(delete_calls) >= 2  # Should delete chunks and source

    def test_thread_safety(self) -> None:
        """Test that the backend is thread-safe."""
        results = []
        
        def worker_thread(thread_id):
            with patch('sqlite3.connect') as mock_connect, \
                 patch.object(SqliteVectorBackend, '_init_database'):
                
                mock_conn = MagicMock()
                mock_connect.return_value = mock_conn
                
                backend = SqliteVectorBackend(
                    db_path=self.db_path,
                    embedding_dimension=self.embedding_dim
                )
                
                # Each thread should get its own connection
                with backend._get_connection():
                    results.append(f"Thread {thread_id} completed")
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(results) == 5
        assert all("completed" in result for result in results)

    @pytest.mark.parametrize("extension", ["auto", "sqlite-vec", "sqlite-vss", "none"])
    def test_different_vector_extensions(self, extension) -> None:
        """Test initialization with different vector extensions."""
        with patch('sqlite3.connect'), \
             patch.object(SqliteVectorBackend, '_init_database'):
            
            backend = SqliteVectorBackend(
                db_path=self.db_path,
                embedding_dimension=self.embedding_dim,
                vector_extension=extension
            )
            
            assert backend.vector_extension == extension

    def test_numpy_availability(self) -> None:
        """Test numpy availability detection."""
        # This tests the module-level numpy import
        from ai_utilities.knowledge.backend import HAS_NUMPY
        
        # Should be a boolean
        assert isinstance(HAS_NUMPY, bool)
        
        # We can't test the actual value since it depends on the environment
        # but we can test that the import doesn't crash
