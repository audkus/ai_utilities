"""
File source loaders for knowledge indexing.

This module provides file loaders for different text file types, supporting
markdown, plain text, Python source files, and logs.
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Dict, List, Set

from .exceptions import KnowledgeValidationError
from .models import Source

logger = logging.getLogger(__name__)


class FileSourceLoader:
    """Loads and extracts text content from various file types."""
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS: Set[str] = {
        '.md',    # Markdown
        '.txt',   # Plain text
        '.py',    # Python source
        '.log',   # Log files
        '.rst',   # reStructuredText
        '.yaml',  # YAML
        '.yml',   # YAML
        '.json',  # JSON
    }
    
    def __init__(self, max_file_size: int = 10 * 1024 * 1024) -> None:
        """
        Initialize the file source loader.
        
        Args:
            max_file_size: Maximum file size to process (default: 10MB)
        """
        self.max_file_size = max_file_size
    
    def is_supported_file(self, path: Path) -> bool:
        """Check if a file type is supported."""
        return path.suffix.lower() in self.SUPPORTED_EXTENSIONS
    
    def load_source(self, path: Path) -> Source:
        """
        Load a file as a knowledge source.
        
        Args:
            path: Path to the file to load
            
        Returns:
            Source object with metadata
        """
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {path}")
        
        if not path.is_file():
            raise KnowledgeValidationError(f"Path is not a file: {path}")
        
        if not self.is_supported_file(path):
            raise KnowledgeValidationError(f"Unsupported file type: {path.suffix}")
        
        if path.stat().st_size > self.max_file_size:
            raise KnowledgeValidationError(
                f"File too large: {path} ({path.stat().st_size} bytes > {self.max_file_size} bytes)"
            )
        
        # Determine loader type based on file extension
        extension = path.suffix.lower()
        if extension == '.md':
            loader_type = 'markdown'
        elif extension == '.py':
            loader_type = 'python'
        elif extension in ['.txt', '.log']:
            loader_type = 'text'
        elif extension in ['.yaml', '.yml']:
            loader_type = 'yaml'
        elif extension == '.json':
            loader_type = 'json'
        elif extension == '.rst':
            loader_type = 'rst'
        else:
            loader_type = 'text'  # Default
        
        return Source.from_path(path, loader_type=loader_type)
    
    def extract_text(self, source: Source) -> str:
        """
        Extract text content from a source.
        
        Args:
            source: The source to extract text from
            
        Returns:
            Extracted text content
            
        Raises:
            KnowledgeValidationError: If text extraction fails
        """
        try:
            with open(source.path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
        except UnicodeDecodeError:
            # Try with different encodings
            encodings = ['latin-1', 'cp1252', 'iso-8859-1']
            content = None
            for encoding in encodings:
                try:
                    with open(source.path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise KnowledgeValidationError(f"Could not decode file: {source.path}")
            
            raw_content = content
        
        # Process content based on file type
        processor = self._get_processor(source.file_extension)
        processed_content = processor(raw_content)
        
        return processed_content
    
    def _get_processor(self, file_extension: str):
        """Get the appropriate content processor for a file extension."""
        processors = {
            'md': self._process_markdown,
            'txt': self._process_plain_text,
            'py': self._process_python,
            'log': self._process_log,
            'rst': self._process_plain_text,
            'yaml': self._process_yaml,
            'yml': self._process_yaml,
            'json': self._process_json,
        }
        
        return processors.get(file_extension, self._process_plain_text)
    
    def _process_markdown(self, content: str) -> str:
        """Process markdown content."""
        # Remove front matter (YAML metadata at the start)
        lines = content.split('\n')
        if lines and lines[0].strip() == '---':
            try:
                end_frontmatter = lines.index('---', 1)
                content = '\n'.join(lines[end_frontmatter + 1:])
            except ValueError:
                # No closing --- found, treat as plain content
                pass
        
        # Remove markdown formatting but preserve structure
        # Remove code blocks
        import re
        content = re.sub(r'```[\s\S]*?```', '', content)
        
        # Remove inline code
        content = re.sub(r'`[^`]+`', '', content)
        
        # Remove links but keep text
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
        
        # Remove images
        content = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', content)
        
        # Remove headers but keep text
        content = re.sub(r'^#+\s+', '', content, flags=re.MULTILINE)
        
        # Remove bold/italic markers
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
        content = re.sub(r'\*([^*]+)\*', r'\1', content)
        content = re.sub(r'__([^_]+)__', r'\1', content)
        content = re.sub(r'_([^_]+)_', r'\1', content)
        
        # Remove list markers
        content = re.sub(r'^\s*[-*+]\s+', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*\d+\.\s+', '', content, flags=re.MULTILINE)
        
        # Remove blockquote markers
        content = re.sub(r'^\s*>\s+', '', content, flags=re.MULTILINE)
        
        # Clean up extra whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = content.strip()
        
        return content
    
    def _process_plain_text(self, content: str) -> str:
        """Process plain text content."""
        # Clean up whitespace while preserving paragraph structure
        import re
        content = re.sub(r'\r\n', '\n', content)
        content = re.sub(r'\r', '\n', content)
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = re.sub(r'[ \t]+', ' ', content)
        return content.strip()
    
    def _process_python(self, content: str) -> str:
        """Process Python source code."""
        try:
            # Parse the AST to extract meaningful content
            tree = ast.parse(content)
            
            # Extract docstrings and comments
            extractor = PythonContentExtractor()
            extractor.visit(tree)
            
            # Combine extracted content with comments
            lines = content.split('\n')
            comments = []
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                # Extract comments
                if '#' in line:
                    comment_start = line.index('#')
                    comment = line[comment_start + 1:].strip()
                    if comment and not comment.startswith('#'):
                        comments.append(comment)
            
            # Combine all content
            all_content = extractor.docstrings + comments
            
            return '\n'.join(all_content)
            
        except SyntaxError:
            # If parsing fails, fall back to comment extraction only
            lines = content.split('\n')
            comments = []
            
            for line in lines:
                if '#' in line:
                    comment_start = line.index('#')
                    comment = line[comment_start + 1:].strip()
                    if comment and not comment.startswith('#'):
                        comments.append(comment)
            
            return '\n'.join(comments)
    
    def _process_log(self, content: str) -> str:
        """Process log files."""
        import re
        
        # Extract meaningful messages from log lines
        lines = content.split('\n')
        messages = []
        
        # Common log patterns
        patterns = [
            r'\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}[^\s]*\s+\w+\s+(.+)',  # Standard timestamp
            r'\[\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\]\s+(.+)',          # Bracketed timestamp
            r'\w+\s+\d+\s+\d{2}:\d{2}:\d{2}\s+(.+)',                        # Syslog format
            r'^\s*\w+\s*:\s*(.+)',                                            # Simple key: value
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    messages.append(match.group(1).strip())
                    break
            else:
                # If no pattern matches, include the line as-is if it looks like a message
                if len(line) > 10 and not line.startswith('===') and not line.startswith('---'):
                    messages.append(line)
        
        return '\n'.join(messages)
    
    def _process_yaml(self, content: str) -> str:
        """Process YAML content."""
        try:
            import yaml
            data = yaml.safe_load(content)
            
            if isinstance(data, dict):
                return self._extract_yaml_text(data)
            elif isinstance(data, list):
                return self._extract_yaml_text({'items': data})
            else:
                return str(data)
                
        except ImportError:
            # YAML library not available, treat as plain text
            return self._process_plain_text(content)
        except Exception:
            # YAML parsing failed, treat as plain text
            return self._process_plain_text(content)
    
    def _process_json(self, content: str) -> str:
        """Process JSON content."""
        try:
            import json
            data = json.loads(content)
            return self._extract_yaml_text(data)
        except ImportError:
            return self._process_plain_text(content)
        except Exception:
            return self._process_plain_text(content)
    
    def _extract_yaml_text(self, data) -> str:
        """Extract text content from YAML/JSON data structure."""
        texts = []
        
        def extract_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    extract_recursive(value, new_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_path = f"{path}[{i}]" if path else f"[{i}]"
                    extract_recursive(item, new_path)
            elif isinstance(obj, str):
                if obj.strip():  # Only include non-empty strings
                    texts.append(obj)
            elif obj is not None:
                texts.append(str(obj))
        
        extract_recursive(data)
        return '\n'.join(texts)


class PythonContentExtractor(ast.NodeVisitor):
    """AST visitor to extract docstrings and meaningful content from Python code."""
    
    def __init__(self) -> None:
        self.docstrings: List[str] = []
    
    def visit_Module(self, node: ast.Module) -> None:
        """Extract module docstring."""
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            self.docstrings.append(node.body[0].value.value.strip())
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Extract function docstring."""
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            self.docstrings.append(node.body[0].value.value.strip())
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Extract class docstring."""
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            self.docstrings.append(node.body[0].value.value.strip())
        self.generic_visit(node)
