"""
Tests for knowledge file source loading.

Tests the file loading and text extraction functionality.
"""

from __future__ import annotations

import pytest
from pathlib import Path

from ai_utilities.knowledge.sources import FileSourceLoader
from ai_utilities.knowledge.exceptions import KnowledgeValidationError


class TestFileSourceLoader:
    """Test the FileSourceLoader class."""
    
    def test_supported_extensions(self) -> None:
        """Test that supported extensions are correctly identified."""
        loader = FileSourceLoader()
        
        supported_extensions = {
            '.md', '.txt', '.py', '.log', '.rst', '.yaml', '.yml', '.json'
        }
        
        assert loader.SUPPORTED_EXTENSIONS == supported_extensions
        
        for ext in supported_extensions:
            assert loader.is_supported_file(Path(f"test{ext}"))
        
        # Test unsupported extensions
        unsupported_files = [
            Path('test.pdf'), Path('test.doc'), Path('test.exe'),
            Path('test.zip'), Path('test.jpg'), Path('test.mp3')
        ]
        
        for file_path in unsupported_files:
            assert not loader.is_supported_file(file_path), f"Should not support {file_path.suffix}"
        
        # Test case insensitivity
        assert loader.is_supported_file(Path('test.MD'))
        assert loader.is_supported_file(Path('test.TXT'))
        assert loader.is_supported_file(Path('test.PY'))
    
    def test_load_source_valid_file(self, tmp_path) -> None:
        """Test loading a valid source file."""
        loader = FileSourceLoader()
        
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!")
        
        source = loader.load_source(test_file)
        
        assert source.source_id == str(test_file)
        assert source.path == test_file.absolute()
        assert source.file_size > 0
        assert source.mime_type == "text/plain"
        assert source.file_extension == "txt"
        assert source.is_text_file is True
    
    def test_load_source_nonexistent_file(self) -> None:
        """Test loading a non-existent file raises error."""
        loader = FileSourceLoader()
        non_existent_file = Path("/non/existent/file.txt")
        
        with pytest.raises(FileNotFoundError):
            loader.load_source(non_existent_file)
    
    def test_load_source_directory(self, tmp_path) -> None:
        """Test loading a directory raises error."""
        loader = FileSourceLoader()
        
        with pytest.raises(KnowledgeValidationError):
            loader.load_source(tmp_path)
    
    def test_load_source_unsupported_type(self, tmp_path) -> None:
        """Test loading an unsupported file type raises error."""
        loader = FileSourceLoader()
        
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"fake pdf content")
        
        with pytest.raises(KnowledgeValidationError, match="Unsupported file type"):
            loader.load_source(test_file)
    
    def test_load_source_file_too_large(self, tmp_path) -> None:
        """Test loading a file that exceeds size limit."""
        small_loader = FileSourceLoader(max_file_size=100)  # Very small limit
        
        test_file = tmp_path / "test.txt"
        content = "This content is definitely larger than 100 bytes. " * 10
        test_file.write_text(content)
        
        with pytest.raises(KnowledgeValidationError, match="File too large"):
            small_loader.load_source(test_file)
    
    def test_load_source_empty_file(self, tmp_path) -> None:
        """Test loading an empty file."""
        loader = FileSourceLoader()
        
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")
        
        source = loader.load_source(test_file)
        
        assert isinstance(source, type(source))  # Source object created
        assert source.source_id is not None
        assert source.path == test_file
        assert source.file_size == 0
        assert source.sha256_hash is not None  # Empty file should still have hash
        assert source.file_extension == "txt"
    
    def test_sha256_hash_stability(self, tmp_path) -> None:
        """Test that SHA256 hash is stable and consistent."""
        loader = FileSourceLoader()
        
        test_file = tmp_path / "test.txt"
        content = "Test content for hash stability"
        test_file.write_text(content)
        
        # Load the same file twice
        source1 = loader.load_source(test_file)
        source2 = loader.load_source(test_file)
        
        # Hash should be the same for same content
        assert source1.sha256_hash == source2.sha256_hash
        assert source1.sha256_hash is not None
        assert len(source1.sha256_hash) == 64  # SHA256 hex length
        
        # Change content and verify hash changes
        test_file.write_text(content + " modified")
        source3 = loader.load_source(test_file)
        assert source3.sha256_hash != source1.sha256_hash
    
    def test_source_key_fields_populated(self, tmp_path) -> None:
        """Test that Source model key fields are properly populated."""
        loader = FileSourceLoader()
        
        test_file = tmp_path / "test.py"
        content = "def test(): pass"
        test_file.write_text(content)
        
        source = loader.load_source(test_file)
        
        # Test key fields are populated
        assert source.source_id is not None
        assert source.path == test_file
        assert source.file_size == len(content.encode('utf-8'))
        assert source.mime_type == "text/x-python"
        assert source.sha256_hash is not None
        assert source.file_extension == "py"
        assert source.is_text_file is True
        assert source.indexed_at is not None  # Should be set to current time
    
    def test_mime_type_detection(self, tmp_path) -> None:
        """Test mime type detection for different file types."""
        loader = FileSourceLoader()
        
        test_cases = [
            ("test.md", "text/markdown"),
            ("test.txt", "text/plain"),
            ("test.py", "text/x-python"),
            ("test.log", "text/plain"),
            ("test.rst", "text/x-rst"),
            ("test.yaml", "text/x-yaml"),
            ("test.yml", "text/x-yaml"),
            ("test.json", "application/json"),
        ]
        
        for filename, expected_mime in test_cases:
            test_file = tmp_path / filename
            test_file.write_text("Test content")
            
            source = loader.load_source(test_file)
            assert source.mime_type == expected_mime, f"Mime type mismatch for {filename}"
    
    def test_extract_text_plain(self, tmp_path) -> None:
        """Test extracting text from plain text files."""
        loader = FileSourceLoader()
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!\n\nThis is a test.")
        
        source = loader.load_source(test_file)
        text = loader.extract_text(source)
        
        assert "Hello, world!" in text
        assert "This is a test." in text
        assert text.strip() == "Hello, world!\n\nThis is a test."
    
    def test_extract_text_markdown(self, tmp_path) -> None:
        """Test extracting text from markdown files."""
        loader = FileSourceLoader()
        
        test_file = tmp_path / "test.md"
        test_file.write_text("""---
title: Test Document
---

# Heading 1

This is a paragraph with **bold** and *italic* text.

## Heading 2

- Item 1
- Item 2

`code inline`

```
code block
```

[Link text](url)
""")
        
        source = loader.load_source(test_file)
        text = loader.extract_text(source)
        
        assert "Heading 1" in text
        assert "Heading 2" in text
        assert "bold" in text
        assert "italic" in text
        assert "Item 1" in text
        assert "Item 2" in text
        assert "code inline" not in text  # Should be removed
        assert "code block" not in text    # Should be removed
        assert "Link text" in text
        assert "url" not in text           # Should be removed
    
    def test_extract_text_python(self, tmp_path) -> None:
        """Test extracting text from Python files."""
        loader = FileSourceLoader()
        
        test_file = tmp_path / "test.py"
        test_file.write_text('''"""Module docstring."""

def test_function():
    """Function docstring."""
    # This is a comment
    return "hello"

class TestClass:
    """Class docstring."""
    
    def method(self):
        """Method docstring."""
        # Another comment
        pass
''')
        
        source = loader.load_source(test_file)
        text = loader.extract_text(source)
        
        assert "Module docstring." in text
        assert "Function docstring." in text
        assert "Class docstring." in text
        assert "Method docstring." in text
        assert "This is a comment" in text
        assert "Another comment" in text
        assert "def test_function" not in text  # Code should be removed
    
    def test_extract_text_log(self, tmp_path) -> None:
        """Test extracting text from log files."""
        loader = FileSourceLoader()
        
        test_file = tmp_path / "test.log"
        test_file.write_text("""2024-01-01 10:00:00 INFO Starting application
2024-01-01 10:00:01 ERROR Failed to connect to database
2024-01-01 10:00:02 WARN Retrying connection
[2024-01-01 10:00:03] Connection established
app: Configuration loaded
""")
        
        source = loader.load_source(test_file)
        text = loader.extract_text(source)
        
        assert "Starting application" in text
        assert "Failed to connect to database" in text
        assert "Retrying connection" in text
        assert "Connection established" in text
        assert "Configuration loaded" in text
    
    def test_extract_text_yaml(self, tmp_path) -> None:
        """Test extracting text from YAML files."""
        loader = FileSourceLoader()
        
        test_file = tmp_path / "test.yaml"
        test_file.write_text("""name: test-app
version: 1.0.0
database:
  host: localhost
  port: 5432
  name: testdb
features:
  - auth
  - logging
  - monitoring
""")
        
        source = loader.load_source(test_file)
        text = loader.extract_text(source)
        
        assert "test-app" in text
        assert "1.0.0" in text
        assert "localhost" in text
        assert "5432" in text
        assert "testdb" in text
        assert "auth" in text
        assert "logging" in text
        assert "monitoring" in text
    
    def test_extract_text_json(self, tmp_path) -> None:
        """Test extracting text from JSON files."""
        loader = FileSourceLoader()
        
        test_file = tmp_path / "test.json"
        test_file.write_text('''{
  "name": "test-app",
  "version": "1.0.0",
  "database": {
    "host": "localhost",
    "port": 5432
  },
  "features": ["auth", "logging"]
}''')
        
        source = loader.load_source(test_file)
        text = loader.extract_text(source)
        
        assert "test-app" in text
        assert "1.0.0" in text
        assert "localhost" in text
        assert "5432" in text
        assert "auth" in text
        assert "logging" in text
    
    def test_extract_text_encoding_fallback(self, tmp_path) -> None:
        """Test text extraction with encoding fallback."""
        loader = FileSourceLoader()
        
        # Create a file with Latin-1 encoding
        test_file = tmp_path / "test.txt"
        content = "Héllo, wörld! ñoño".encode('latin-1')
        test_file.write_bytes(content)
        
        source = loader.load_source(test_file)
        text = loader.extract_text(source)
        
        assert "Héllo" in text
        assert "wörld" in text
        assert "ñoño" in text
    
    def test_extract_empty_file(self, tmp_path) -> None:
        """Test extracting text from an empty file."""
        loader = FileSourceLoader()
        
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")
        
        source = loader.load_source(test_file)
        text = loader.extract_text(source)
        
        assert text == ""
    
    def test_source_from_path_unknown_extension(self, tmp_path) -> None:
        """Test Source.from_path with unknown extension gets fallback mime type."""
        from ai_utilities.knowledge.models import Source
        
        test_file = tmp_path / "test.unknown"
        test_file.write_text("Some content")
        
        source = Source.from_path(test_file)
        
        # Should get default mime type for unknown extensions
        assert source.mime_type == "application/octet-stream"
        assert source.file_extension == "unknown"
        assert source.is_text_file is False
    
    def test_file_size_calculation(self, tmp_path) -> None:
        """Test that file size is calculated correctly."""
        loader = FileSourceLoader()
        
        test_file = tmp_path / "size_test.txt"
        content = "Test content for size calculation"
        test_file.write_text(content)
        
        source = loader.load_source(test_file)
        
        # File size should match actual bytes
        expected_size = len(content.encode('utf-8'))
        assert source.file_size == expected_size
    
    def test_git_commit_detection_non_failing(self, tmp_path) -> None:
        """Test git commit detection doesn't fail outside git repos."""
        loader = FileSourceLoader()
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        source = loader.load_source(test_file)
        
        # Git commit should be None if not in git repo (or could be set if in git)
        # The important thing is that it doesn't fail
        assert source.git_commit is None or isinstance(source.git_commit, str)
    
    @pytest.mark.parametrize("content,expected_substrings", [
        ("Héllo wörld! ñoño", ["Héllo", "wörld", "ñoño"]),
        ("🚀 Rocket launch! 🌟", ["🚀", "Rocket", "🌟"]),
        ("Café naïve résumé", ["Café", "naïve", "résumé"]),
    ])
    def test_unicode_content_handling(self, tmp_path, content, expected_substrings) -> None:
        """Test loading files with unicode content."""
        loader = FileSourceLoader()
        
        test_file = tmp_path / "unicode.txt"
        test_file.write_text(content)
        
        source = loader.load_source(test_file)
        text = loader.extract_text(source)
        
        # Check that unicode characters are preserved
        for substring in expected_substrings:
            assert substring in text
    
    @pytest.mark.parametrize("content", [
        "Special chars: !@#$%^&*()",
        "Quotes: 'single' and \"double\"",
        "Math: 2 + 2 = 4, π ≈ 3.14159",
        "Tabs\tand\nnewlines",
    ])
    def test_special_characters_content(self, tmp_path, content) -> None:
        """Test loading files with special characters."""
        loader = FileSourceLoader()
        
        test_file = tmp_path / "special.txt"
        test_file.write_text(content)
        
        source = loader.load_source(test_file)
        text = loader.extract_text(source)
        
        # For tabs/newlines, check that the content is preserved (may be normalized)
        if "\t" in content or "\n" in content:
            # Check that tabs and newlines are present in some form
            assert "Tabs" in text and "and" in text and "newlines" in text
        else:
            assert content in text
    
    def test_file_path_with_spaces(self, tmp_path) -> None:
        """Test loading files with spaces in path."""
        loader = FileSourceLoader()
        
        test_file = tmp_path / "test file with spaces.txt"
        content = "Content in file with spaces in path"
        test_file.write_text(content)
        
        source = loader.load_source(test_file)
        assert source.path == test_file
        assert content in loader.extract_text(source)
