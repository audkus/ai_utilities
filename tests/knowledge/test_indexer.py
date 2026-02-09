"""
Tests for knowledge indexer.

Tests the knowledge indexing functionality.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from ai_utilities.knowledge.backend import SqliteVectorBackend
from ai_utilities.knowledge.chunking import TextChunker
from ai_utilities.knowledge.exceptions import KnowledgeIndexError
from ai_utilities.knowledge.indexer import KnowledgeIndexer
from ai_utilities.knowledge.sources import FileSourceLoader
from tests.knowledge.fake_embeddings import FakeEmbeddingProvider


class TestKnowledgeIndexer:
    """Test the KnowledgeIndexer class."""

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory for testing."""
        with TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def temp_db(self, temp_dir) -> Path:
        """Create a temporary database file."""
        return temp_dir / "test.db"

    @pytest.fixture
    def indexer(self, temp_db) -> KnowledgeIndexer:
        """Create an indexer instance for testing."""
        backend = SqliteVectorBackend(
            db_path=temp_db,
            embedding_dimension=10,
            vector_extension="none",
        )

        file_loader = FileSourceLoader(max_file_size=1024 * 1024)
        chunker = TextChunker(chunk_size=100, chunk_overlap=20, min_chunk_size=10)
        embedding_client = FakeEmbeddingProvider(embedding_dimension=10)

        return KnowledgeIndexer(
            backend=backend,
            file_loader=file_loader,
            chunker=chunker,
            embedding_client=embedding_client,
            embedding_model="test-model",
        )

    @pytest.fixture
    def sample_files(self, temp_dir) -> list[Path]:
        """Create sample files for testing."""
        files = []

        # Create test files
        test_files = {
            "test1.txt": "This is the first test file. It contains some text to be indexed.",
            "test2.md": """# Markdown File
            
This is a markdown file with **bold** text.
            
## Section 2
            
More content here.
""",
            "test3.py": '''"""Python module."""

def test_function():
    """Test function docstring."""
    return "hello"

# This is a comment
class TestClass:
    pass
''',
        }

        for filename, content in test_files.items():
            file_path = temp_dir / filename
            file_path.write_text(content)
            files.append(file_path)

        return files

    def test_indexer_initialization(self, indexer) -> None:
        """Test indexer initialization."""
        assert indexer.backend is not None
        assert indexer.file_loader is not None
        assert indexer.chunker is not None
        assert indexer.embedding_client is not None
        assert indexer.embedding_model == "test-model"

    def test_index_single_file(self, indexer, sample_files) -> None:
        """Test indexing a single file."""
        file_path = sample_files[0]

        stats = indexer.index_files([file_path])

        assert stats["total_files"] == 1
        assert stats["processed_files"] == 1
        assert stats["skipped_files"] == 0
        assert stats["error_files"] == 0
        assert stats["total_chunks"] > 0
        assert stats["total_embeddings"] > 0
        assert stats["processing_time"] > 0
        assert len(stats["errors"]) == 0

    def test_index_multiple_files(self, indexer, sample_files) -> None:
        """Test indexing multiple files."""
        stats = indexer.index_files(sample_files)

        assert stats["total_files"] == len(sample_files)
        assert stats["processed_files"] == len(sample_files)
        assert stats["skipped_files"] == 0
        assert stats["error_files"] == 0
        assert stats["total_chunks"] > 0
        assert stats["total_embeddings"] > 0

    def test_index_directory(self, indexer, temp_dir) -> None:
        """Test indexing a directory."""
        # Create test files
        test_file1 = temp_dir / "test1.txt"
        test_file1.write_text("This is a test document about machine learning.")

        test_file2 = temp_dir / "test2.txt"
        test_file2.write_text("Python is great for data science and AI applications.")

        stats = indexer.index_directory(temp_dir)

        assert stats["processed_files"] > 0
        assert stats["total_chunks"] > 0
        assert stats["total_embeddings"] > 0

    def test_index_empty_directory(self, indexer, temp_dir) -> None:
        """Test indexing an empty directory."""
        # temp_dir is already empty
        stats = indexer.index_directory(temp_dir)

        assert stats["processed_files"] == 0
        assert stats["total_files"] == 0
        assert stats["skipped_files"] == 0
        assert stats["error_files"] == 0

    def test_index_nonexistent_directory(self, indexer) -> None:
        """Test indexing a non-existent directory raises error."""
        with pytest.raises(KnowledgeIndexError):
            indexer.index_directory(Path("/nonexistent/directory"))

    def test_index_not_a_directory(self, indexer, temp_dir) -> None:
        """Test indexing a path that's not a directory raises error."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("test")

        with pytest.raises(KnowledgeIndexError):
            indexer.index_directory(file_path)

    def test_index_unsupported_file(self, indexer, temp_dir) -> None:
        """Test indexing an unsupported file type."""
        file_path = temp_dir / "test.pdf"
        file_path.write_bytes(b"fake pdf content")

        stats = indexer.index_files([file_path])

        assert stats["total_files"] == 1
        assert stats["processed_files"] == 0
        assert stats["error_files"] == 1
        assert len(stats["errors"]) == 1

    def test_index_empty_file(self, indexer, temp_dir) -> None:
        """Test indexing an empty file."""
        file_path = temp_dir / "empty.txt"
        file_path.write_text("")

        stats = indexer.index_files([file_path])

        assert stats["total_files"] == 1
        assert stats["skipped_files"] == 1
        assert stats["processed_files"] == 0

    def test_index_too_small_file(self, indexer, temp_dir) -> None:
        """Test indexing a file that's too small after chunking."""
        file_path = temp_dir / "tiny.txt"
        file_path.write_text("x")  # Very small content

        stats = indexer.index_files([file_path])

        assert stats["total_files"] == 1
        assert stats["skipped_files"] == 1
        assert stats["processed_files"] == 0

    def test_force_reindex(self, indexer, sample_files) -> None:
        """Test force reindexing existing files."""
        file_path = sample_files[0]

        # Index file first time
        stats1 = indexer.index_files([file_path])
        assert stats1["processed_files"] == 1

        # Index same file without force (should be skipped)
        stats2 = indexer.index_files([file_path], force_reindex=False)
        assert stats2["skipped_files"] == 1
        assert stats2["processed_files"] == 0

        # Index with force (should reprocess)
        stats3 = indexer.index_files([file_path], force_reindex=True)
        assert stats3["processed_files"] == 1

    def test_reindex_changed_files(self, indexer, temp_dir) -> None:
        """Test reindexing only changed files."""
        # Create initial files
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("Original content 1")
        file2.write_text("Original content 2")

        # Initial index
        indexer.index_directory(temp_dir)

        # Modify one file
        file1.write_text("Modified content 1")

        # Reindex changed files
        stats2 = indexer.reindex_changed_files(temp_dir)

        # Should only reindex the changed file
        assert stats2["processed_files"] == 1
        assert stats2["skipped_files"] == 1

    def test_remove_source(self, indexer, sample_files) -> None:
        """Test removing a source from the index."""
        file_path = sample_files[0]

        # Index file
        indexer.index_files([file_path])

        # Verify chunks exist
        chunks = indexer.backend.get_source_chunks(str(file_path))
        assert len(chunks) > 0

        # Remove source
        result = indexer.remove_source(file_path)
        assert result is True

        # Verify chunks are gone
        chunks = indexer.backend.get_source_chunks(str(file_path))
        assert len(chunks) == 0

        # Try to remove non-existent source
        result = indexer.remove_source(Path("/nonexistent/file.txt"))
        assert result is False

    def test_get_index_stats(self, indexer, sample_files) -> None:
        """Test getting index statistics."""
        # Initial stats
        stats = indexer.get_index_stats()
        assert "backend" in stats
        assert "chunker" in stats
        assert "embedding" in stats

        # Index some files
        indexer.index_files(sample_files)

        # Updated stats
        stats = indexer.get_index_stats()
        assert stats["backend"]["chunks_count"] > 0
        assert stats["backend"]["embeddings_count"] > 0
        assert stats["chunker"]["chunk_size"] == 100
        assert stats["chunker"]["chunk_overlap"] == 20
        assert stats["embedding"]["model"] == "test-model"
        assert stats["embedding"]["dimension"] == 10

    def test_embedding_generation_error(self, temp_db) -> None:
        """Test handling of embedding generation errors."""
        backend = SqliteVectorBackend(
            db_path=temp_db,
            embedding_dimension=10,
            vector_extension="none",
        )

        file_loader = FileSourceLoader()
        chunker = TextChunker()

        # Create a faulty embedding client
        class FaultyEmbeddingClient:
            def get_embeddings(self, texts, model=None):
                raise Exception("Embedding failed")

        indexer = KnowledgeIndexer(
            backend=backend,
            file_loader=file_loader,
            chunker=chunker,
            embedding_client=FaultyEmbeddingClient(),
            embedding_model="test-model",
        )

        # Create a test file
        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            file_path.write_text(
                "This is a longer test content for indexing that should definitely create chunks and trigger the embedding generation error."
            )

            # Should raise KnowledgeIndexError
            with pytest.raises(KnowledgeIndexError):
                indexer.index_files([file_path], force_reindex=True)

    def test_chunking_error_handling(self, temp_db) -> None:
        """Test handling of chunking errors."""
        backend = SqliteVectorBackend(
            db_path=temp_db,
            embedding_dimension=10,
            vector_extension="none",
        )

        # Create a faulty chunker
        class FaultyChunker:
            def chunk_text(self, text, source_id, start_chunk_index=0):
                raise Exception("Chunking failed")

        indexer = KnowledgeIndexer(
            backend=backend,
            file_loader=FileSourceLoader(),
            chunker=FaultyChunker(),
            embedding_client=FakeEmbeddingProvider(),
            embedding_model="test-model",
        )

        # Create a test file
        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            file_path.write_text(
                "This is a longer test content for indexing that should definitely create chunks and trigger the chunking error."
            )

            # Should raise KnowledgeIndexError
            with pytest.raises(KnowledgeIndexError):
                indexer.index_files([file_path], force_reindex=True)
