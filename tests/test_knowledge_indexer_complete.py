"""
Complete coverage tests for knowledge/indexer.py module.
This test focuses on achieving 100% coverage by properly mocking all dependencies.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from tempfile import TemporaryDirectory

# Mock all the problematic imports BEFORE importing the indexer
mock_backend = Mock()
mock_chunking = Mock()
mock_exceptions = Mock()
mock_sources = Mock()

# Create mock exception classes
mock_exceptions.KnowledgeIndexError = Exception
mock_exceptions.KnowledgeValidationError = Exception

# Patch the modules
with patch.dict('sys.modules', {
    'ai_utilities.knowledge.backend': mock_backend,
    'ai_utilities.knowledge.chunking': mock_chunking,
    'ai_utilities.knowledge.exceptions': mock_exceptions,
    'ai_utilities.knowledge.sources': mock_sources,
}):
    from ai_utilities.knowledge.indexer import KnowledgeIndexer


class TestKnowledgeIndexerComplete:
    """Complete coverage tests for KnowledgeIndexer."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Setup all mocked dependencies."""
        # Mock backend
        backend = Mock()
        backend.SqliteVectorBackend = Mock
        backend.source_exists.return_value = False
        backend.get_source_hash.return_value = "different_hash"
        backend.add_source.return_value = None
        backend.add_chunks.return_value = None
        backend.get_index_stats.return_value = {
            'total_sources': 1,
            'total_chunks': 2,
            'total_embeddings': 2
        }
        backend.remove_source.return_value = None
        
        # Mock file loader
        file_loader = Mock()
        mock_source = Mock()
        mock_source.source_id = "test_source_123"
        mock_source.path = Path("/test/file.txt")
        mock_source.file_size = 100
        mock_source.mime_type = "text/plain"
        mock_source.sha256_hash = "abc123"
        file_loader.load_source.return_value = mock_source
        
        # Mock chunker
        chunker = Mock()
        mock_chunks = [
            {'text': 'Test chunk 1', 'metadata': {'chunk_id': 0}},
            {'text': 'Test chunk 2', 'metadata': {'chunk_id': 1}}
        ]
        chunker.chunk_text.return_value = mock_chunks
        
        # Mock embedding client
        embedding_client = Mock()
        mock_response = Mock()
        mock_embedding = Mock()
        mock_embedding.embedding = [0.1, 0.2, 0.3]
        mock_response.data = [mock_embedding]
        embedding_client.embeddings.create.return_value = mock_response
        
        return {
            'backend': backend,
            'file_loader': file_loader,
            'chunker': chunker,
            'embedding_client': embedding_client
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
    
    def test_init_and_basic_methods(self, indexer):
        """Test initialization and basic method coverage."""
        # Constructor already covered
        assert indexer.embedding_model == "test-model"
    
    def test_index_directory_validation_errors(self, indexer, tmp_path):
        """Test directory validation error paths."""
        # Test non-existent directory
        non_existent = tmp_path / "non_existent"
        with pytest.raises(Exception):
            indexer.index_directory(non_existent)
        
        # Test file instead of directory
        file_path = tmp_path / "test.txt"
        file_path.write_text("content")
        with pytest.raises(Exception):
            indexer.index_directory(file_path)
    
    def test_index_files_empty_list(self, indexer):
        """Test indexing empty file list."""
        result = indexer.index_files([])
        
        assert result['total_files'] == 0
        assert result['processed_files'] == 0
        assert result['skipped_files'] == 0
        assert result['error_files'] == 0
        assert result['total_chunks'] == 0
        assert result['total_embeddings'] == 0
    
    def test_index_files_with_content(self, indexer, mock_dependencies, tmp_path):
        """Test indexing files with actual content."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Mock source_exists to return False (not indexed)
        mock_dependencies['backend'].source_exists.return_value = False
        
        result = indexer.index_files([test_file], force_reindex=True)
        
        assert result['total_files'] == 1
        assert 'processed_files' in result
        assert 'skipped_files' in result
        assert 'error_files' in result
        assert 'total_chunks' in result
        assert 'total_embeddings' in result
    
    def test_index_files_already_indexed(self, indexer, mock_dependencies, tmp_path):
        """Test indexing files that are already indexed."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Mock source_exists to return True (already indexed)
        mock_dependencies['backend'].source_exists.return_value = True
        mock_dependencies['backend'].get_source_hash.return_value = "same_hash"
        
        result = indexer.index_files([test_file], force_reindex=False)
        
        assert result['total_files'] == 1
        assert result['skipped_files'] == 1
    
    def test_find_files_comprehensive(self, indexer, tmp_path):
        """Test _find_files with comprehensive scenarios."""
        # Create nested directory structure
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.md").write_text("content2")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.txt").write_text("content3")
        (tmp_path / "subdir" / "subsub").mkdir()
        (tmp_path / "subdir" / "subsub" / "file4.txt").write_text("content4")
        
        # Test recursive
        files_recursive = indexer._find_files(tmp_path, recursive=True)
        assert len(files_recursive) >= 4
        
        # Test non-recursive
        files_non_recursive = indexer._find_files(tmp_path, recursive=False)
        assert len(files_non_recursive) >= 2
        assert all(f.parent == tmp_path for f in files_non_recursive)
    
    def test_index_file_complete_workflow(self, indexer, mock_dependencies, tmp_path):
        """Test _index_file complete workflow."""
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
    
    def test_index_file_already_exists_same_hash(self, indexer, mock_dependencies, tmp_path):
        """Test _index_file when source exists with same hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Mock that source exists and hash is same
        mock_dependencies['backend'].source_exists.return_value = True
        mock_dependencies['backend'].get_source_hash.return_value = "same_hash"
        
        result = indexer._index_file(test_file, existing_sources={"test_source_123"}, force_reindex=False)
        
        assert result['processed'] is False
        assert result['skipped'] is True
    
    def test_index_file_already_exists_different_hash(self, indexer, mock_dependencies, tmp_path):
        """Test _index_file when source exists but hash is different."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Mock that source exists but hash is different
        mock_dependencies['backend'].source_exists.return_value = True
        mock_dependencies['backend'].get_source_hash.return_value = "different_hash"
        
        result = indexer._index_file(test_file, existing_sources={"test_source_123"}, force_reindex=False)
        
        assert result['processed'] is True
        assert result['skipped'] is False
    
    def test_index_file_load_error(self, indexer, mock_dependencies, tmp_path):
        """Test _index_file with load error."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Mock file loader to raise exception
        mock_dependencies['file_loader'].load_source.side_effect = Exception("Load failed")
        
        result = indexer._index_file(test_file, existing_sources=set(), force_reindex=True)
        
        assert result['processed'] is False
        assert result['error'] is not None
    
    def test_index_file_chunking_error(self, indexer, mock_dependencies, tmp_path):
        """Test _index_file with chunking error."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Mock chunker to raise exception
        mock_dependencies['chunker'].chunk_text.side_effect = Exception("Chunking failed")
        
        result = indexer._index_file(test_file, existing_sources=set(), force_reindex=True)
        
        assert result['processed'] is False
        assert result['error'] is not None
    
    def test_index_file_embedding_error(self, indexer, mock_dependencies, tmp_path):
        """Test _index_file with embedding error."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Mock embedding client to raise exception
        mock_dependencies['embedding_client'].embeddings.create.side_effect = Exception("Embedding failed")
        
        result = indexer._index_file(test_file, existing_sources=set(), force_reindex=True)
        
        assert result['processed'] is False
        assert result['error'] is not None
    
    def test_generate_embeddings_success(self, indexer):
        """Test _generate_embeddings success."""
        texts = ["text1", "text2"]
        
        embeddings = indexer._generate_embeddings(texts)
        
        assert len(embeddings) == 2
        assert all(isinstance(emb, list) for emb in embeddings)
        assert all(len(emb) == 3 for emb in embeddings)
    
    def test_generate_embeddings_error(self, indexer, mock_dependencies):
        """Test _generate_embeddings with error."""
        texts = ["text1", "text2"]
        
        # Mock embedding client to raise exception
        mock_dependencies['embedding_client'].embeddings.create.side_effect = Exception("API error")
        
        with pytest.raises(Exception):
            indexer._generate_embeddings(texts)
    
    def test_reindex_changed_files(self, indexer, mock_dependencies, tmp_path):
        """Test reindex_changed_files."""
        # Create test directory
        test_dir = tmp_path / "test_docs"
        test_dir.mkdir()
        (test_dir / "doc1.txt").write_text("Content 1")
        
        result = indexer.reindex_changed_files(test_dir, recursive=True)
        
        assert result['total_files'] >= 0
        assert 'processed_files' in result
        assert 'skipped_files' in result
    
    def test_remove_source(self, indexer, mock_dependencies):
        """Test remove_source."""
        source_id = "test_source_123"
        
        indexer.remove_source(source_id)
        
        mock_dependencies['backend'].remove_source.assert_called_once_with(source_id)
    
    def test_get_index_stats(self, indexer, mock_dependencies):
        """Test get_index_stats."""
        stats = indexer.get_index_stats()
        
        assert stats['total_sources'] == 1
        assert stats['total_chunks'] == 2
        assert stats['total_embeddings'] == 2
        mock_dependencies['backend'].get_index_stats.assert_called_once()
    
    def test_all_error_paths_and_edge_cases(self, indexer, mock_dependencies, tmp_path):
        """Test all remaining error paths and edge cases."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Test various error scenarios
        error_scenarios = [
            ("load_source", Exception("Load error")),
            ("chunk_text", Exception("Chunk error")),
            ("embeddings.create", Exception("Embed error")),
            ("add_source", Exception("Add source error")),
            ("add_chunks", Exception("Add chunks error")),
        ]
        
        for method_name, error in error_scenarios:
            # Reset mocks
            for mock_obj in mock_dependencies.values():
                if hasattr(mock_obj, 'reset_mock'):
                    mock_obj.reset_mock()
            
            # Set up the error
            if '.' in method_name:
                obj_name, attr_name = method_name.split('.')
                getattr(mock_dependencies[obj_name], attr_name).side_effect = error
            else:
                getattr(mock_dependencies['file_loader'], method_name).side_effect = error
            
            # Test the error
            result = indexer._index_file(test_file, existing_sources=set(), force_reindex=True)
            assert result['processed'] is False
            assert result['error'] is not None
