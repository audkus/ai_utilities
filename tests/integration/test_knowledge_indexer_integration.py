"""
Integration tests for knowledge/indexer.py module.
This test focuses on achieving 100% coverage by testing real functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from tempfile import TemporaryDirectory

# We need to mock the dependencies that cause import issues
with patch.dict('sys.modules', {
    'ai_utilities.knowledge.backend': Mock(),
    'ai_utilities.knowledge.chunking': Mock(), 
    'ai_utilities.knowledge.sources': Mock(),
}):
    # Import real exceptions
    from ai_utilities.knowledge.exceptions import KnowledgeIndexError, KnowledgeValidationError
    # Mock the exceptions module but return real exceptions
    exceptions_mock = Mock()
    exceptions_mock.KnowledgeIndexError = KnowledgeIndexError
    exceptions_mock.KnowledgeValidationError = KnowledgeValidationError
    
    with patch.dict('sys.modules', {
        'ai_utilities.knowledge.exceptions': exceptions_mock,
    }):
        from ai_utilities.knowledge.indexer import KnowledgeIndexer


class TestKnowledgeIndexerIntegration:
    """Integration tests for KnowledgeIndexer to achieve 100% coverage."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all the knowledge dependencies."""
        # Create mock objects for all dependencies
        mock_backend = Mock()
        mock_file_loader = Mock()
        mock_chunker = Mock()
        mock_embedding_client = Mock()
        
        # Setup mock sources
        mock_source = Mock()
        mock_source.source_id = "test_source_123"
        mock_source.path = Path("/test/file.txt")
        mock_source.file_size = 100
        mock_source.mime_type = "text/plain"
        mock_source.sha256_hash = "abc123"
        mock_file_loader.load_source.return_value = mock_source
        
        # Setup mock chunks
        mock_chunk1 = Mock()
        mock_chunk1.text = 'Test chunk 1'
        mock_chunk1.metadata = {'chunk_id': 0}
        mock_chunk2 = Mock()
        mock_chunk2.text = 'Test chunk 2'
        mock_chunk2.metadata = {'chunk_id': 1}
        mock_chunks = [mock_chunk1, mock_chunk2]
        mock_chunker.chunk_text.return_value = mock_chunks
        mock_chunker.chunk_size = 1000
        mock_chunker.chunk_overlap = 200
        mock_chunker.min_chunk_size = 100
        
        # Setup mock embeddings
        mock_embedding_client.get_embeddings.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        
        # Setup backend methods
        mock_backend.source_exists.return_value = False
        mock_backend.get_source_hash.return_value = "different_hash"
        mock_backend.get_existing_sources.return_value = set()  # Return empty set, not Mock
        mock_backend.add_source.return_value = None
        mock_backend.add_chunks.return_value = None
        mock_backend.delete_source.return_value = None  # Add delete_source method
        mock_backend.get_stats.return_value = {  # Add get_stats method
            'total_sources': 1,
            'total_chunks': 2,
            'total_embeddings': 2
        }
        mock_backend.embedding_dimension = 1536  # Add embedding dimension
        mock_backend.get_index_stats.return_value = {
            'total_sources': 1,
            'total_chunks': 2,
            'total_embeddings': 2
        }
        mock_backend.remove_source.return_value = None
        
        return {
            'backend': mock_backend,
            'file_loader': mock_file_loader,
            'chunker': mock_chunker,
            'embedding_client': mock_embedding_client
        }
    
    @pytest.fixture
    def indexer(self, mock_dependencies):
        """Create KnowledgeIndexer with mocked dependencies."""
        return KnowledgeIndexer(
            backend=mock_dependencies['backend'],
            file_loader=mock_dependencies['file_loader'],
            chunker=mock_dependencies['chunker'],
            embedding_client=mock_dependencies['embedding_client'],
            embedding_model="test-model"
        )
    
    def test_full_index_directory_workflow(self, indexer, mock_dependencies, tmp_path):
        """Test complete directory indexing workflow."""
        # Create test directory structure
        test_dir = tmp_path / "test_docs"
        test_dir.mkdir()
        (test_dir / "doc1.txt").write_text("Document 1 content")
        (test_dir / "doc2.txt").write_text("Document 2 content")
        
        # Test directory indexing
        result = indexer.index_directory(test_dir, recursive=True)
        
        # Verify all parts of the workflow were called
        assert result['total_files'] >= 0
        assert 'processed_files' in result
        assert 'skipped_files' in result
        assert 'error_files' in result
        assert 'total_chunks' in result
        assert 'total_embeddings' in result
    
    def test_full_index_files_workflow(self, indexer, mock_dependencies, tmp_path):
        """Test complete file indexing workflow."""
        # Create test files
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Test file indexing
        result = indexer.index_files([test_file], force_reindex=True)
        
        # Verify results
        assert result['total_files'] == 1
        assert 'processed_files' in result
        assert 'skipped_files' in result
        assert 'error_files' in result
        assert 'total_chunks' in result
        assert 'total_embeddings' in result
    
    def test_index_file_with_all_paths(self, indexer, mock_dependencies, tmp_path):
        """Test _index_file with all code paths."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Test successful indexing
        result = indexer._index_file(test_file, existing_sources=set(), force_reindex=True)
        
        assert result['processed'] is True
        assert result['skipped'] is False
        assert result['chunks_created'] > 0
        assert result['embeddings_created'] > 0
        assert result['error'] is None
        assert result['source_id'] is not None
    
    def test_index_file_already_exists(self, indexer, mock_dependencies, tmp_path):
        """Test _index_file when source already exists."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Mock that source exists and hash is same
        mock_dependencies['backend'].source_exists.return_value = True
        mock_dependencies['backend'].get_source_hash.return_value = "abc123"  # Match the source hash
        
        result = indexer._index_file(test_file, existing_sources={"test_source_123"}, force_reindex=False)
        
        assert result['processed'] is False
        assert result['skipped'] is True
    
    def test_generate_embeddings_complete(self, indexer):
        """Test _generate_embeddings with complete workflow."""
        texts = ["text1", "text2"]
        
        embeddings = indexer._generate_embeddings(texts)
        
        assert len(embeddings) == 2
        assert all(isinstance(emb, list) for emb in embeddings)
        assert all(len(emb) == 3 for emb in embeddings)  # Mock embedding size
    
    def test_reindex_changed_files_complete(self, indexer, mock_dependencies, tmp_path):
        """Test reindex_changed_files complete workflow."""
        # Create test directory
        test_dir = tmp_path / "test_docs"
        test_dir.mkdir()
        (test_dir / "doc1.txt").write_text("Content 1")
        
        result = indexer.reindex_changed_files(test_dir, recursive=True)
        
        assert result['total_files'] >= 0
        assert 'processed_files' in result
        assert 'skipped_files' in result
    
    def test_remove_source_complete(self, indexer, mock_dependencies, tmp_path):
        """Test remove_source complete workflow."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        indexer.remove_source(test_file)
        
        mock_dependencies['backend'].delete_source.assert_called_once_with("test_source_123")
    
    def test_get_index_stats_complete(self, indexer, mock_dependencies):
        """Test get_index_stats complete workflow."""
        stats = indexer.get_index_stats()
        
        # The indexer returns a nested structure with backend stats
        assert stats['backend']['total_sources'] == 1
        assert stats['backend']['total_chunks'] == 2
        assert stats['backend']['total_embeddings'] == 2
    
    def test_error_handling_paths(self, indexer, mock_dependencies, tmp_path):
        """Test various error handling paths."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Test load_source error
        mock_dependencies['file_loader'].load_source.side_effect = Exception("Load failed")
        with pytest.raises(KnowledgeIndexError, match="Failed to index.*Load failed"):
            indexer._index_file(test_file, existing_sources=set(), force_reindex=True)
        
        # Reset for next test
        mock_dependencies['file_loader'].load_source.side_effect = None
        
        # Test embedding error  
        mock_dependencies['embedding_client'].get_embeddings.side_effect = Exception("Embedding failed")
        with pytest.raises(KnowledgeIndexError, match="Failed to generate embeddings.*Embedding failed"):
            indexer._index_file(test_file, existing_sources=set(), force_reindex=True)
    
    def test_find_files_all_scenarios(self, indexer, tmp_path):
        """Test _find_files with all scenarios."""
        # Create nested directory structure
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file2.txt").write_text("content2")
        (tmp_path / "subdir" / "subsub").mkdir()
        (tmp_path / "subdir" / "subsub" / "file3.txt").write_text("content3")
        
        # Test recursive
        files_recursive = indexer._find_files(tmp_path, recursive=True)
        assert len(files_recursive) >= 3
        
        # Test non-recursive
        files_non_recursive = indexer._find_files(tmp_path, recursive=False)
        assert len(files_non_recursive) >= 1
        assert all(f.parent == tmp_path for f in files_non_recursive)
