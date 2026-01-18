"""
Comprehensive tests for knowledge/sources.py module.
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from ai_utilities.knowledge.sources import FileSourceLoader
from ai_utilities.knowledge.models import Source
from ai_utilities.knowledge.exceptions import KnowledgeValidationError


class TestFileSourceLoader:
    """Comprehensive tests for FileSourceLoader class."""
    
    def test_init_default_parameters(self):
        """Test FileSourceLoader initialization with default parameters."""
        loader = FileSourceLoader()
        assert loader.max_file_size == 10 * 1024 * 1024  # 10MB
        assert loader.SUPPORTED_EXTENSIONS == {
            '.md', '.txt', '.py', '.log', '.rst', '.yaml', '.yml', '.json'
        }
    
    def test_init_custom_parameters(self):
        """Test FileSourceLoader initialization with custom parameters."""
        custom_size = 5 * 1024 * 1024  # 5MB
        loader = FileSourceLoader(max_file_size=custom_size)
        assert loader.max_file_size == custom_size
    
    def test_is_supported_file(self):
        """Test file extension support checking."""
        loader = FileSourceLoader()
        
        # Test supported extensions
        supported_files = [
            Path('test.md'), Path('test.txt'), Path('test.py'),
            Path('test.log'), Path('test.rst'), Path('test.yaml'),
            Path('test.yml'), Path('test.json')
        ]
        
        for file_path in supported_files:
            assert loader.is_supported_file(file_path), f"Should support {file_path.suffix}"
        
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
    
    def test_load_source_markdown_file(self):
        """Test loading markdown files."""
        loader = FileSourceLoader()
        
        with TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.md"
            content = "# Test Markdown\n\nThis is a **test** markdown file with some content."
            test_file.write_text(content)
            
            source = loader.load_source(test_file)
            
            assert isinstance(source, Source)
            assert source.source_id is not None
            assert source.path == test_file
            assert source.file_size == len(content.encode('utf-8'))
            assert source.mime_type == "text/markdown"
            assert source.sha256_hash is not None
            assert len(source.sha256_hash) == 64  # SHA256 hex length
            assert source.text_content == content
    
    def test_load_source_text_file(self):
        """Test loading plain text files."""
        loader = FileSourceLoader()
        
        with TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.txt"
            content = "This is a plain text file.\nIt has multiple lines.\nAnd some content."
            test_file.write_text(content)
            
            source = loader.load_source(test_file)
            
            assert isinstance(source, Source)
            assert source.source_id is not None
            assert source.path == test_file
            assert source.file_size == len(content.encode('utf-8'))
            assert source.mime_type == "text/plain"
            assert source.sha256_hash is not None
            assert source.text_content == content
    
    def test_load_source_python_file(self):
        """Test loading Python source files."""
        loader = FileSourceLoader()
        
        with TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.py"
            content = '''def hello_world():
    """A simple hello world function."""
    print("Hello, World!")
    return True

if __name__ == "__main__":
    hello_world()
'''
            test_file.write_text(content)
            
            source = loader.load_source(test_file)
            
            assert isinstance(source, Source)
            assert source.source_id is not None
            assert source.path == test_file
            assert source.file_size == len(content.encode('utf-8'))
            assert source.mime_type == "text/x-python"
            assert source.sha256_hash is not None
            assert source.text_content == content
    
    def test_load_source_log_file(self):
        """Test loading log files."""
        loader = FileSourceLoader()
        
        with TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.log"
            content = '''2024-01-13 10:00:00 INFO Application started
2024-01-13 10:01:00 DEBUG Processing request
2024-01-13 10:02:00 ERROR Something went wrong
2024-01-13 10:03:00 INFO Application stopped
'''
            test_file.write_text(content)
            
            source = loader.load_source(test_file)
            
            assert isinstance(source, Source)
            assert source.source_id is not None
            assert source.path == test_file
            assert source.file_size == len(content.encode('utf-8'))
            assert source.mime_type == "text/plain"  # .log files treated as plain text
            assert source.sha256_hash is not None
            assert source.text_content == content
    
    def test_load_source_rst_file(self):
        """Test loading reStructuredText files."""
        loader = FileSourceLoader()
        
        with TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.rst"
            content = '''Test Document
=============

This is a reStructuredText document.

* Item 1
* Item 2
* Item 3
'''
            test_file.write_text(content)
            
            source = loader.load_source(test_file)
            
            assert isinstance(source, Source)
            assert source.source_id is not None
            assert source.path == test_file
            assert source.file_size == len(content.encode('utf-8'))
            assert source.mime_type == "text/x-rst"
            assert source.sha256_hash is not None
            assert source.text_content == content
    
    def test_load_source_yaml_file(self):
        """Test loading YAML files."""
        loader = FileSourceLoader()
        
        with TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.yaml"
            content = '''name: test-app
version: 1.0.0
config:
  debug: true
  port: 8080
features:
  - auth
  - logging
  - metrics
'''
            test_file.write_text(content)
            
            source = loader.load_source(test_file)
            
            assert isinstance(source, Source)
            assert source.source_id is not None
            assert source.path == test_file
            assert source.file_size == len(content.encode('utf-8'))
            assert source.mime_type == "text/x-yaml"
            assert source.sha256_hash is not None
            assert source.text_content == content
    
    def test_load_source_json_file(self):
        """Test loading JSON files."""
        loader = FileSourceLoader()
        
        with TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.json"
            content = '''{
  "name": "test-app",
  "version": "1.0.0",
  "config": {
    "debug": true,
    "port": 8080
  },
  "features": ["auth", "logging", "metrics"]
}'''
            test_file.write_text(content)
            
            source = loader.load_source(test_file)
            
            assert isinstance(source, Source)
            assert source.source_id is not None
            assert source.path == test_file
            assert source.file_size == len(content.encode('utf-8'))
            assert source.mime_type == "application/json"
            assert source.sha256_hash is not None
            assert source.text_content == content
    
    def test_load_source_file_not_exists(self):
        """Test loading a file that doesn't exist."""
        loader = FileSourceLoader()
        non_existent_file = Path("/non/existent/file.txt")
        
        with pytest.raises(FileNotFoundError):
            loader.load_source(non_existent_file)
    
    def test_load_source_unsupported_file_type(self):
        """Test loading an unsupported file type."""
        loader = FileSourceLoader()
        
        with TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.pdf"
            test_file.write_text("Fake PDF content")
            
            with pytest.raises(KnowledgeValidationError, match="Unsupported file type"):
                loader.load_source(test_file)
    
    def test_load_source_file_too_large(self):
        """Test loading a file that exceeds size limit."""
        small_loader = FileSourceLoader(max_file_size=100)  # Very small limit
        
        with TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.txt"
            content = "This content is definitely larger than 100 bytes. " * 10
            test_file.write_text(content)
            
            with pytest.raises(KnowledgeValidationError, match="File too large"):
                small_loader.load_source(test_file)
    
    def test_load_source_empty_file(self):
        """Test loading an empty file."""
        loader = FileSourceLoader()
        
        with TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "empty.txt"
            test_file.write_text("")
            
            source = loader.load_source(test_file)
            
            assert isinstance(source, Source)
            assert source.source_id is not None
            assert source.path == test_file
            assert source.file_size == 0
            assert source.text_content == ""
            assert source.sha256_hash is not None  # Empty file should still have hash
    
    def test_load_source_binary_file(self):
        """Test loading a binary file (should be rejected)."""
        loader = FileSourceLoader()
        
        with TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "binary.txt"
            # Write some binary data
            with open(test_file, 'wb') as f:
                f.write(b'\x00\x01\x02\x03\x04\x05\xff\xfe')
            
            # Should handle binary files gracefully (either process or reject)
            try:
                source = loader.load_source(test_file)
                # If processed, should handle encoding properly
                assert isinstance(source, Source)
            except (UnicodeDecodeError, KnowledgeValidationError):
                # If rejected, that's also acceptable
                pass
    
    def test_load_source_unicode_content(self):
        """Test loading files with unicode content."""
        loader = FileSourceLoader()
        
        with TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "unicode.txt"
            content = "Unicode test: café, naïve, résumé, 北京, Москва, emoji: 🚀 🌟 ✨"
            test_file.write_text(content, encoding='utf-8')
            
            source = loader.load_source(test_file)
            
            assert isinstance(source, Source)
            assert source.text_content == content
            assert "café" in source.text_content
            assert "北京" in source.text_content
            assert "🚀" in source.text_content
    
    def test_load_source_special_characters(self):
        """Test loading files with special characters."""
        loader = FileSourceLoader()
        
        with TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "special.txt"
            content = "Special chars: \t\n\r\\\"'!@#$%^&*()[]{}|;:,.<>?"
            test_file.write_text(content)
            
            # Read back the content as written (file system normalizes \r to \n)
            expected_content = test_file.read_text()
            
            source = loader.load_source(test_file)
            
            assert isinstance(source, Source)
            assert source.text_content == expected_content
    
    def test_load_source_path_with_spaces(self):
        """Test loading files with spaces in path."""
        loader = FileSourceLoader()
        
        with TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test file with spaces.txt"
            content = "Content from file with spaces in name"
            test_file.write_text(content)
            
            source = loader.load_source(test_file)
            
            assert isinstance(source, Source)
            assert source.path == test_file
            assert source.text_content == content
    
    def test_load_source_python_syntax_extraction(self):
        """Test that Python files preserve syntax highlighting info."""
        loader = FileSourceLoader()
        
        with TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "syntax.py"
            content = '''import os
import sys

class TestClass:
    """A test class."""
    
    def __init__(self, name: str):
        self.name = name
    
    def greet(self) -> str:
        return f"Hello, {self.name}!"

# Test function
def main():
    obj = TestClass("World")
    print(obj.greet())

if __name__ == "__main__":
    main()
'''
            test_file.write_text(content)
            
            source = loader.load_source(test_file)
            
            assert isinstance(source, Source)
            assert source.text_content == content
            # Verify that all Python syntax is preserved
            assert "import os" in source.text_content
            assert "class TestClass:" in source.text_content
            assert '"""A test class."""' in source.text_content
            assert 'f"Hello, {self.name}!"' in source.text_content
    
    def test_source_id_consistency(self):
        """Test that source_id is consistent for the same file."""
        loader = FileSourceLoader()
        
        with TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "consistency.txt"
            content = "Test content for consistency check"
            test_file.write_text(content)
            
            # Load the same file twice
            source1 = loader.load_source(test_file)
            source2 = loader.load_source(test_file)
            
            # Source IDs should be the same (based on path and hash)
            assert source1.source_id == source2.source_id
            assert source1.sha256_hash == source2.sha256_hash
    
    def test_mime_type_detection(self):
        """Test mime type detection for different file types."""
        loader = FileSourceLoader()
        
        with TemporaryDirectory() as tmp_dir:
            test_cases = [
                ("test.md", "text/markdown"),
                ("test.txt", "text/plain"),
                ("test.py", "text/x-python"),
                ("test.log", "text/plain"),
                ("test.rst", "text/x-rst"),
                ("test.yaml", "application/x-yaml"),
                ("test.yml", "application/x-yaml"),
                ("test.json", "application/json"),
            ]
            
            for filename, expected_mime in test_cases:
                test_file = Path(tmp_dir) / filename
                test_file.write_text("Test content")
                
                source = loader.load_source(test_file)
                assert source.mime_type == expected_mime, f"Mime type mismatch for {filename}"
