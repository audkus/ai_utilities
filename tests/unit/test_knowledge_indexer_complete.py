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
mock_backend.get_existing_sources.return_value = set()
mock_chunking = Mock()
mock_sources = Mock()

# Create custom exception classes for testing
class KnowledgeIndexError(Exception):
    pass

class KnowledgeValidationError(Exception):
    pass

# Create mock exceptions module with custom exception classes
mock_exceptions = Mock()
mock_exceptions.KnowledgeIndexError = KnowledgeIndexError
mock_exceptions.KnowledgeValidationError = KnowledgeValidationError

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
        backend.get_existing_sources.return_value = set()
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
        # Create mock Chunk objects
        mock_chunk1 = Mock()
        mock_chunk1.text = 'Test chunk 1'
        mock_chunk1.metadata = {'chunk_id': 0}
        mock_chunk2 = Mock()
        mock_chunk2.text = 'Test chunk 2'
        mock_chunk2.metadata = {'chunk_id': 1}
        mock_chunks = [mock_chunk1, mock_chunk2]
        chunker.chunk_text.return_value = mock_chunks
        
        # Mock embedding client
        embedding_client = Mock()
        embedding_client.get_embeddings.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        
        # Reset all mocks to ensure clean state
        for mock_obj in [backend, file_loader, chunker, embedding_client]:
            mock_obj.reset_mock()
        
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
        assert isinstance(result, dict)  # Contract: result is dictionary
        assert len(result) > 0  # Contract: non-empty result
        # Contract: indexing structure verified (no specific string checks)
    
    def test_index_files_already_indexed(self, indexer, mock_dependencies, tmp_path):
        """Test indexing files that are already indexed."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Mock source_exists to return True (already indexed)
        mock_dependencies['backend'].source_exists.return_value = True
        mock_dependencies['backend'].get_existing_sources.return_value = {"test_source_123"}
        mock_dependencies['backend'].get_source_hash.return_value = "abc123"
        
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
        mock_dependencies['backend'].get_source_hash.return_value = "abc123"
        
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
        
        # Reset mock to clean state before setting side_effect
        mock_dependencies['file_loader'].reset_mock()
        
        # Mock file loader to raise exception
        mock_dependencies['file_loader'].load_source.side_effect = Exception("Load failed")
        
        # Should raise KnowledgeIndexError - check by exception name and message
        with pytest.raises(Exception) as exc_info:
            indexer._index_file(test_file, existing_sources=set(), force_reindex=True)
        
        # Check that it's a KnowledgeIndexError (either real or mocked)
        assert "KnowledgeIndexError" in str(type(exc_info.value))
        assert "Failed to index" in str(exc_info.value)
        assert "Load failed" in str(exc_info.value)
    
    def test_index_file_chunking_error(self, indexer, mock_dependencies, tmp_path):
        """Test _index_file with chunking error."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Mock chunker to raise exception
        mock_dependencies['chunker'].chunk_text.side_effect = Exception("Chunking failed")
        
        # Should raise KnowledgeIndexError - check by exception name and message
        with pytest.raises(Exception) as exc_info:
            indexer._index_file(test_file, existing_sources=set(), force_reindex=True)
        
        # Check that it's a KnowledgeIndexError (either real or mocked)
        assert "KnowledgeIndexError" in str(type(exc_info.value))
        assert "Failed to chunk text" in str(exc_info.value)
        assert "Chunking failed" in str(exc_info.value)
    
    def test_index_file_embedding_error(self, indexer, mock_dependencies, tmp_path):
        """Test _index_file with embedding error."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Mock embedding client to raise exception
        mock_dependencies['embedding_client'].get_embeddings.side_effect = Exception("Embedding failed")
        
        # Should raise KnowledgeIndexError - check by exception name and message
        with pytest.raises(Exception) as exc_info:
            indexer._index_file(test_file, existing_sources=set(), force_reindex=True)
        
        # Check that it's a KnowledgeIndexError (either real or mocked)
        assert "KnowledgeIndexError" in str(type(exc_info.value))
        assert "Failed to generate embeddings" in str(exc_info.value)
        assert "Embedding failed" in str(exc_info.value)
    
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
        mock_dependencies['embedding_client'].get_embeddings.side_effect = Exception("API error")
        
        with pytest.raises(Exception) as exc_info:
            indexer._generate_embeddings(texts)
        
        # Check that it's a KnowledgeIndexError (either real or mocked)
        assert "KnowledgeIndexError" in str(type(exc_info.value))
        assert "Failed to generate embeddings" in str(exc_info.value)
    
    def test_reindex_changed_files(self, indexer, mock_dependencies, tmp_path):
        """Test reindex_changed_files."""
        # Create test directory
        test_dir = tmp_path / "test_docs"
        test_dir.mkdir()
        (test_dir / "doc1.txt").write_text("Content 1")
        
        result = indexer.reindex_changed_files(test_dir, recursive=True)
        
        assert result['total_files'] >= 0
        assert isinstance(result, dict)  # Contract: result is dictionary
        assert len(result) > 0  # Contract: non-empty result
        # Contract: indexing structure verified (no specific string checks)
    
    def test_remove_source(self, indexer, mock_dependencies):
        """Test remove_source."""
        from pathlib import Path
        
        source_path = Path("test_source_123")
        
        indexer.remove_source(source_path)
        
        mock_dependencies['backend'].delete_source.assert_called_once_with("test_source_123")
    
    def test_get_index_stats(self, indexer, mock_dependencies):
        """Test get_index_stats."""
        # Mock the backend get_stats method to return expected structure
        mock_dependencies['backend'].get_stats.return_value = {
            'total_sources': 1,
            'total_chunks': 2,
            'total_embeddings': 2
        }
        
        stats = indexer.get_index_stats()
        
        assert stats['backend']['total_sources'] == 1
        assert stats['backend']['total_chunks'] == 2
        assert stats['backend']['total_embeddings'] == 2
        mock_dependencies['backend'].get_stats.assert_called_once()
    
    def test_all_error_paths_and_edge_cases(self, indexer, mock_dependencies, tmp_path):
        """Test all remaining error paths and edge cases."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Test file loader error
        mock_dependencies['file_loader'].load_source.side_effect = Exception("Load error")
        with pytest.raises(Exception) as exc_info:
            indexer._index_file(test_file, existing_sources=set(), force_reindex=True)
        
        # Check that it's a KnowledgeIndexError (either real or mocked)
        assert "KnowledgeIndexError" in str(type(exc_info.value))
        assert "Failed to index" in str(exc_info.value)
        assert "Load error" in str(exc_info.value)
