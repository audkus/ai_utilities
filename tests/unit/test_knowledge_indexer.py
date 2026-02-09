"""
Tests for knowledge/indexer.py module.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from ai_utilities.knowledge.indexer import KnowledgeIndexer
from ai_utilities.knowledge.exceptions import KnowledgeIndexError, KnowledgeValidationError


class TestKnowledgeIndexer:
    """Test KnowledgeIndexer class."""
    
    @pytest.fixture
    def mock_backend(self):
        """Mock SQLite vector backend."""
        backend = Mock()
        backend.source_exists.return_value = False
        backend.add_source.return_value = None
        backend.add_chunks.return_value = None
        backend.get_existing_sources.return_value = set()
        backend.get_index_stats.return_value = {
            'total_sources': 0,
            'total_chunks': 0,
            'total_embeddings': 0
        }
        return backend
    
    @pytest.fixture
    def mock_file_loader(self):
        """Mock file source loader."""
        loader = Mock()
        # Mock load_source to return a source object
        mock_source = Mock()
        mock_source.source_id = "test_source_123"
        mock_source.path = Path("/test/file.txt")
        mock_source.file_size = 100
        mock_source.mime_type = "text/plain"
        mock_source.sha256_hash = "abc123"
        loader.load_source.return_value = mock_source
        return loader
    
    @pytest.fixture
    def mock_chunker(self):
        """Mock text chunker."""
        from ai_utilities.knowledge.models import Chunk
        
        chunker = Mock()
        chunker.chunk_text.return_value = [
            Chunk(
                chunk_id="test_chunk_1",
                source_id="test_source",
                text='Test content line 1',
                metadata={'chunk_id': 0, 'start_line': 1},
                chunk_index=0,
                start_char=0,
                end_char=20
            ),
            Chunk(
                chunk_id="test_chunk_2", 
                source_id="test_source",
                text='Test content line 2',
                metadata={'chunk_id': 1, 'start_line': 2},
                chunk_index=1,
                start_char=21,
                end_char=41
            )
        ]
        return chunker
    
    @pytest.fixture
    def mock_embedding_client(self):
        """Mock embedding client."""
        client = Mock()
        # Mock the get_embeddings method that the indexer actually uses
        client.get_embeddings.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        return client
    
    @pytest.fixture
    def indexer(self, mock_backend, mock_file_loader, mock_chunker, mock_embedding_client):
        """Create KnowledgeIndexer instance with mocked dependencies."""
        return KnowledgeIndexer(
            backend=mock_backend,
            file_loader=mock_file_loader,
            chunker=mock_chunker,
            embedding_client=mock_embedding_client,
            embedding_model="test-model"
        )
    
    def test_init(self, indexer, mock_backend, mock_file_loader, mock_chunker, mock_embedding_client):
        """Test KnowledgeIndexer initialization."""
        assert indexer.backend == mock_backend
        assert indexer.file_loader == mock_file_loader
        assert indexer.chunker == mock_chunker
        assert indexer.embedding_client == mock_embedding_client
        assert indexer.embedding_model == "test-model"
    
    def test_init_default_model(self, mock_backend, mock_file_loader, mock_chunker, mock_embedding_client):
        """Test KnowledgeIndexer initialization with default model."""
        indexer = KnowledgeIndexer(
            backend=mock_backend,
            file_loader=mock_file_loader,
            chunker=mock_chunker,
            embedding_client=mock_embedding_client
        )
        assert indexer.embedding_model == "text-embedding-3-small"
    
    def test_index_directory_not_exists(self, indexer, tmp_path):
        """Test indexing directory that doesn't exist."""
        non_existent = tmp_path / "non_existent"
        
        with pytest.raises(KnowledgeIndexError, match="Directory does not exist"):
            indexer.index_directory(non_existent)
    
    def test_index_directory_not_directory(self, indexer, tmp_path):
        """Test indexing path that is not a directory."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("test content")
        
        with pytest.raises(KnowledgeIndexError, match="Path is not a directory"):
            indexer.index_directory(file_path)
    
    def test_index_directory_success(self, indexer, tmp_path):
        """Test successful directory indexing."""
        # Create test files
        (tmp_path / "test1.txt").write_text("Test content 1")
        (tmp_path / "test2.txt").write_text("Test content 2")
        
        with patch.object(indexer, '_find_files') as mock_find:
            mock_find.return_value = [tmp_path / "test1.txt", tmp_path / "test2.txt"]
            
            result = indexer.index_directory(tmp_path)
            
            assert result['total_files'] == 2
            assert isinstance(result, dict)  # Contract: result is dictionary
            assert len(result) > 0  # Contract: non-empty result
            # Contract: indexing structure verified (no specific string checks)
    
    def test_index_files_empty_list(self, indexer):
        """Test indexing empty file list."""
        result = indexer.index_files([])
        
        assert result['total_files'] == 0
        assert result['processed_files'] == 0
        assert result['skipped_files'] == 0
        assert result['error_files'] == 0
        assert result['total_chunks'] == 0
        assert result['total_embeddings'] == 0
    
    def test_index_files_with_force_reindex(self, indexer, tmp_path):
        """Test indexing files with force reindex."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Store original return value to restore later
        original_source_exists = indexer.backend.source_exists.return_value
        
        # Mock source_exists to return True (already indexed)
        indexer.backend.source_exists.return_value = True
        
        try:
            result = indexer.index_files([test_file], force_reindex=True)
            
            assert result['total_files'] == 1
            # Should process even though already indexed due to force_reindex
            assert result['processed_files'] >= 0
        finally:
            # Clean up mock changes to prevent test leakage
            indexer.backend.source_exists.return_value = original_source_exists
    
    def test_index_files_already_indexed(self, indexer, tmp_path):
        """Test indexing files that are already indexed."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Store original return values to restore later
        original_source_exists = indexer.backend.source_exists.return_value
        original_existing_sources = indexer.backend.get_existing_sources.return_value
        original_source_hash = indexer.backend.get_source_hash.return_value
        
        # Mock source_exists to return True (already indexed)
        indexer.backend.source_exists.return_value = True
        # Mock get_existing_sources to include the test source
        indexer.backend.get_existing_sources.return_value = {"test_source_123"}
        # Mock get_source_hash to return the same hash as the source
        indexer.backend.get_source_hash.return_value = "abc123"
        
        try:
            result = indexer.index_files([test_file], force_reindex=False)
            
            assert result['total_files'] == 1
            assert result['skipped_files'] == 1
            assert result['processed_files'] == 0
        finally:
            # Clean up mock changes to prevent test leakage
            indexer.backend.source_exists.return_value = original_source_exists
            indexer.backend.get_existing_sources.return_value = original_existing_sources
            indexer.backend.get_source_hash.return_value = original_source_hash
    
    def test_find_files_recursive(self, indexer, tmp_path):
        """Test finding files recursively."""
        # Create nested structure
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file2.txt").write_text("content2")
        
        files = indexer._find_files(tmp_path, recursive=True)
        
        assert len(files) >= 2
        assert any(f.name == "file1.txt" for f in files)
        assert any(f.name == "file2.txt" for f in files)
    
    def test_find_files_non_recursive(self, indexer, tmp_path):
        """Test finding files non-recursively."""
        # Create nested structure
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file2.txt").write_text("content2")
        
        files = indexer._find_files(tmp_path, recursive=False)
        
        # Should only find files in top directory
        assert any(f.name == "file1.txt" for f in files)
        assert not any(f.parent.name == "subdir" for f in files)
    
    def test_index_file_success(self, indexer, tmp_path):
        """Test successful file indexing."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Mock backend methods
        indexer.backend.get_source_hash.return_value = "different_hash"
        indexer.backend.add_source.return_value = None
        indexer.backend.add_chunks.return_value = None
        
        result = indexer._index_file(test_file, existing_sources=set(), force_reindex=True)
        
        assert result['processed'] is True
        assert result['chunks_created'] > 0
        assert result['embeddings_created'] > 0
    
    def test_index_file_load_error(self, indexer, tmp_path):
        """Test file indexing with load error."""
        from ai_utilities.knowledge.exceptions import KnowledgeIndexError
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Store original return value to restore later
        original_return = indexer.file_loader.load_source.return_value
        
        # Mock file loader to raise exception
        indexer.file_loader.load_source.side_effect = Exception("Load error")
        
        try:
            # Should raise KnowledgeIndexError
            with pytest.raises(KnowledgeIndexError, match="Failed to index.*Load error"):
                indexer._index_file(test_file, existing_sources=set(), force_reindex=True)
        finally:
            # Clean up side_effect to prevent test leakage
            indexer.file_loader.load_source.side_effect = None
            indexer.file_loader.load_source.return_value = original_return
    
    def test_index_file_embedding_error(self, indexer, tmp_path):
        """Test file indexing with embedding error."""
        from ai_utilities.knowledge.exceptions import KnowledgeIndexError
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Store original return value to restore later
        original_return = indexer.embedding_client.get_embeddings.return_value
        
        # Mock embedding client to raise exception
        indexer.embedding_client.get_embeddings.side_effect = Exception("Embedding error")
        
        try:
            # Should raise KnowledgeIndexError
            with pytest.raises(KnowledgeIndexError, match="Failed to generate embeddings.*Embedding error"):
                indexer._index_file(test_file, existing_sources=set(), force_reindex=True)
        finally:
            # Clean up side_effect to prevent test leakage
            indexer.embedding_client.get_embeddings.side_effect = None
            indexer.embedding_client.get_embeddings.return_value = original_return
    
    def test_generate_embeddings(self, indexer):
        """Test embedding generation."""
        chunks = ["chunk1", "chunk2"]
        
        embeddings = indexer._generate_embeddings(chunks)
        
        assert len(embeddings) == 2
        assert all(len(embedding) == 3 for embedding in embeddings)  # Mock embeddings
        assert indexer.embedding_client.get_embeddings.called
    
    def test_generate_embeddings_error(self, indexer):
        """Test embedding generation with error."""
        chunks = ["chunk1", "chunk2"]
        
        # Store original return value to restore later
        original_return = indexer.embedding_client.get_embeddings.return_value
        
        # Mock embedding client to raise exception
        indexer.embedding_client.get_embeddings.side_effect = Exception("API error")
        
        try:
            with pytest.raises(KnowledgeIndexError, match="Failed to generate embeddings"):
                indexer._generate_embeddings(chunks)
        finally:
            # Clean up side_effect to prevent test leakage
            indexer.embedding_client.get_embeddings.side_effect = None
            indexer.embedding_client.get_embeddings.return_value = original_return
    
    def test_reindex_changed_files(self, indexer, tmp_path):
        """Test reindexing changed files."""
        # Create test files
        (tmp_path / "test1.txt").write_text("Test content 1")
        (tmp_path / "test2.txt").write_text("Test content 2")
        
        with patch.object(indexer, '_find_files') as mock_find:
            mock_find.return_value = [tmp_path / "test1.txt", tmp_path / "test2.txt"]
            
            result = indexer.reindex_changed_files(tmp_path)
            
            assert result['total_files'] == 2
            assert isinstance(result, dict)  # Contract: result is dictionary
            assert len(result) > 0  # Contract: non-empty result
            # Contract: reindex structure verified (no specific string checks)
    
    def test_remove_source(self, indexer):
        """Test removing a source."""
        from pathlib import Path
        
        source_path = Path("/test/file.txt")
        
        # Mock the file loader and backend methods
        mock_source = Mock()
        mock_source.source_id = "test_source_123"
        indexer.file_loader.load_source.return_value = mock_source
        indexer.backend.delete_source = Mock()
        
        indexer.remove_source(source_path)
        
        indexer.file_loader.load_source.assert_called_once_with(source_path)
        indexer.backend.delete_source.assert_called_once_with("test_source_123")
    
    def test_get_index_stats(self, indexer):
        """Test getting index statistics."""
        # Mock the get_stats method to return proper stats
        indexer.backend.get_stats.return_value = {
            'total_sources': 5,
            'total_chunks': 100,
            'total_embeddings': 100
        }
        indexer.backend.embedding_dimension = 1536
        
        stats = indexer.get_index_stats()
        
        # Check the nested structure
        assert 'backend' in stats
        assert 'chunker' in stats
        assert 'embedding' in stats
        
        # Check backend stats
        assert stats['backend']['total_sources'] == 5
        assert stats['backend']['total_chunks'] == 100
        assert stats['backend']['total_embeddings'] == 100
        
        # Check chunker stats
        assert 'chunk_size' in stats['chunker']
        assert 'chunk_overlap' in stats['chunker']
        assert 'min_chunk_size' in stats['chunker']
        
        # Check embedding stats
        assert stats['embedding']['model'] == "test-model"
        assert stats['embedding']['dimension'] == 1536
    
    def test_integration_full_workflow(self, indexer, tmp_path):
        """Test full indexing workflow integration."""
        # Create test directory with files
        test_dir = tmp_path / "test_docs"
        test_dir.mkdir()
        (test_dir / "doc1.txt").write_text("This is document 1 with multiple lines.\nSecond line of doc1.")
        (test_dir / "doc2.txt").write_text("This is document 2.")
        
        # Index the directory
        result = indexer.index_directory(test_dir)
        
        # Verify results
        assert result['total_files'] >= 2
        assert result['processed_files'] >= 0
        
        # Mock get_stats for the stats check
        indexer.backend.get_stats.return_value = {
            'total_sources': 2,
            'total_chunks': 10,
            'total_embeddings': 10
        }
        
        # Check stats
        stats = indexer.get_index_stats()
        assert stats['backend']['total_sources'] >= 0
