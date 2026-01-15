"""
Pydantic models for knowledge indexing and search.

This module defines the core data structures used throughout the knowledge system:
- Source: Represents a file or document source
- Chunk: Represents a text chunk from a source
- SearchHit: Represents a search result with similarity score
"""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, computed_field, ConfigDict


class Source(BaseModel):
    """Represents a source document or file."""
    
    # Identification
    source_id: str = Field(description="Unique identifier for the source")
    path: Path = Field(description="File system path to the source")
    
    # Metadata
    file_size: int = Field(description="Size of the file in bytes")
    mime_type: str = Field(description="MIME type of the file")
    loader_type: Optional[str] = Field(default=None, description="Type of loader used for this source")
    git_commit: Optional[str] = Field(default=None, description="Git commit hash if file is in a git repository")
    
    # Change detection
    mtime: datetime = Field(description="File modification time")
    sha256_hash: str = Field(description="SHA256 hash of file content")
    
    # Indexing metadata
    indexed_at: datetime = Field(default_factory=datetime.utcnow, description="When source was indexed")
    chunk_count: int = Field(default=0, description="Number of chunks created from this source")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            Path: lambda v: str(v),
        }
    )
    
    @computed_field
    @property
    def file_extension(self) -> str:
        """File extension without the dot."""
        return self.path.suffix.lstrip('.').lower()
    
    @computed_field
    @property
    def is_text_file(self) -> bool:
        """Whether this is a supported text file type."""
        return self.file_extension in {'md', 'txt', 'py', 'log', 'rst', 'yaml', 'yml', 'json'}
    
    @classmethod
    def from_path(cls, path: Path, loader_type: Optional[str] = None) -> Source:
        """Create a Source from a file path, computing metadata."""
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {path}")
        
        stat = path.stat()
        
        # Compute SHA256 hash
        sha256_hash = sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        # Determine MIME type
        extension = path.suffix.lower()
        mime_types = {
            '.md': 'text/markdown',
            '.txt': 'text/plain',
            '.py': 'text/x-python',
            '.log': 'text/plain',
            '.rst': 'text/x-rst',
            '.yaml': 'text/x-yaml',
            '.yml': 'text/x-yaml',
            '.json': 'application/json',
        }
        mime_type = mime_types.get(extension, 'application/octet-stream')
        
        # Try to get git commit if file is in a git repository
        git_commit = None
        try:
            import subprocess
            # Get the git commit for this file
            result = subprocess.run(
                ['git', 'log', '-n', '1', '--format=%H', '--', str(path)],
                capture_output=True,
                text=True,
                cwd=path.parent
            )
            if result.returncode == 0 and result.stdout.strip():
                git_commit = result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            # Git not available or not in a git repo
            pass
        
        # If no loader_type specified, infer from file extension
        if loader_type is None:
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
        
        return cls(
            source_id=str(path),
            path=path.absolute(),
            file_size=stat.st_size,
            mime_type=mime_type,
            loader_type=loader_type,
            git_commit=git_commit,
            mtime=datetime.fromtimestamp(stat.st_mtime),
            sha256_hash=sha256_hash.hexdigest(),
        )


class Chunk(BaseModel):
    """Represents a text chunk from a source document."""
    
    # Identification
    chunk_id: str = Field(description="Unique identifier for the chunk")
    source_id: str = Field(description="ID of the source this chunk belongs to")
    
    # Content
    text: str = Field(description="Text content of the chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional chunk metadata")
    
    # Position information
    chunk_index: int = Field(description="Index of this chunk within the source")
    start_char: int = Field(description="Character position where chunk starts")
    end_char: int = Field(description="Character position where chunk ends")
    
    # Embedding
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding of the chunk text")
    embedding_model: Optional[str] = Field(default=None, description="Model used to create the embedding")
    embedded_at: Optional[datetime] = Field(default=None, description="When embedding was created")
    embedding_dimensions: Optional[int] = Field(default=None, description="Dimensions of the embedding vector")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )
    
    @computed_field
    @property
    def text_length(self) -> int:
        """Length of the chunk text."""
        return len(self.text)
    
    @computed_field
    @property
    def has_embedding(self) -> bool:
        """Whether this chunk has an embedding."""
        return self.embedding is not None and len(self.embedding) > 0
    
    @computed_field
    @property
    def embedding_dimension(self) -> Optional[int]:
        """Dimension of the embedding if present."""
        return len(self.embedding) if self.embedding else None


class SearchHit(BaseModel):
    """Represents a search result with similarity information."""
    
    # Content
    chunk: Chunk = Field(description="The matching chunk")
    text: str = Field(description="Text content (convenience field)")
    
    # Search metrics
    similarity_score: float = Field(description="Cosine similarity score (0-1, higher is better)")
    rank: int = Field(description="Rank in search results (1-based)")
    
    # Source information
    source_path: Path = Field(description="Path to the source file")
    source_type: str = Field(description="Type of the source file")
    
    model_config = ConfigDict(
        json_encoders={
            Path: lambda v: str(v),
        }
    )
    
    @computed_field
    @property
    def is_high_similarity(self) -> bool:
        """Whether this hit has high similarity (>0.8)."""
        return self.similarity_score > 0.8
    
    @computed_field
    @property
    def is_medium_similarity(self) -> bool:
        """Whether this hit has medium similarity (0.5-0.8)."""
        return 0.5 <= self.similarity_score <= 0.8
    
    @classmethod
    def from_chunk(cls, chunk: Chunk, similarity_score: float, rank: int, source_path: Union[str, Path]) -> SearchHit:
        """Create a SearchHit from a Chunk with search metrics."""
        # Convert to Path if string
        if isinstance(source_path, str):
            source_path = Path(source_path)
        
        return cls(
            chunk=chunk,
            text=chunk.text,
            similarity_score=similarity_score,
            rank=rank,
            source_path=source_path,
            source_type=source_path.suffix.lstrip('.').lower(),
        )
