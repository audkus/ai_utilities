"""
SQLite vector storage backend with extension support.

This module provides vector storage and similarity search using SQLite,
with optional support for sqlite-vec or sqlite-vss extensions for KNN search.
"""

from __future__ import annotations
import json
import logging
import sqlite3
import struct
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Tuple, Dict, Literal

# Optional numpy import for optimized vector operations
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

from .exceptions import SqliteExtensionUnavailableError
from .models import Chunk, Source


class SqliteVectorBackend:
    """SQLite backend for vector storage and similarity search."""
    
    def __init__(
        self,
        db_path: Path,
        embedding_dimension: int,
        vector_extension: Literal["auto", "sqlite-vec", "sqlite-vss", "none"] = "auto",
    ) -> None:
        """
        Initialize the SQLite vector backend.
        
        Args:
            db_path: Path to the SQLite database file
            embedding_dimension: Dimension of the embeddings
            vector_extension: Which vector extension to use:
                - "auto": Try sqlite-vec first, then sqlite-vss, then fallback
                - "sqlite-vec": Use sqlite-vec extension or fail
                - "sqlite-vss": Use sqlite-vss extension or fail  
                - "none": Use pure Python fallback mode
        """
        self.db_path = db_path
        self.embedding_dimension = embedding_dimension
        self.vector_extension = vector_extension
        self._extension_available = False
        self._extension_name = None
        self._fallback_reason = None
        self._local = threading.local()
        
        # Initialize database
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """Get a thread-local database connection."""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
            )
            # Enable foreign keys
            self._local.connection.execute("PRAGMA foreign_keys = ON")
            # Optimize for vector operations
            self._local.connection.execute("PRAGMA journal_mode = WAL")
            self._local.connection.execute("PRAGMA synchronous = NORMAL")
            self._local.connection.execute("PRAGMA cache_size=10000")
            self._local.connection.execute("PRAGMA temp_store=memory")
        
        try:
            yield self._local.connection
        except Exception:
            self._local.connection.rollback()
            raise
    
    def _init_database(self) -> None:
        """Initialize the database schema."""
        with self._get_connection() as conn:
            # Create sources table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    source_id TEXT PRIMARY KEY,
                    path TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    mime_type TEXT,
                    loader_type TEXT,
                    git_commit TEXT,
                    mtime REAL NOT NULL,
                    sha256_hash TEXT NOT NULL,
                    indexed_at REAL NOT NULL,
                    chunk_count INTEGER DEFAULT 0
                )
            """)
            
            # Create chunks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    metadata TEXT,
                    chunk_index INTEGER NOT NULL,
                    start_char INTEGER NOT NULL,
                    end_char INTEGER NOT NULL,
                    embedding_model TEXT,
                    embedded_at REAL,
                    embedding_dimensions INTEGER,
                    FOREIGN KEY (source_id) REFERENCES sources (source_id)
                )
            """)
            
            # Create embeddings table based on extension availability
            self._try_load_extension(conn)
            
            if self._extension_available:
                self._create_extension_tables(conn)
                logging.info(f"Using {self._extension_name} extension for vector operations")
            else:
                # Fallback: store embeddings as BLOB in chunks table
                try:
                    conn.execute("""
                        ALTER TABLE chunks ADD COLUMN embedding BLOB
                    """)
                except sqlite3.OperationalError:
                    # Column already exists
                    pass
                
                if self._fallback_reason:
                    if self.vector_extension == "none":
                        # User explicitly chose no extension, use info level
                        logging.info(
                            f"Using pure Python fallback mode (vector_extension='none').\n"
                            f"Reason: {self._fallback_reason}"
                        )
                    else:
                        # User wanted an extension but it wasn't available
                        logging.warning(
                            f"SQLite vector extension unavailable → using pure Python fallback.\n"
                            f"Reason: {self._fallback_reason}\n"
                            f"To improve performance, install an extension:\n"
                            f"  • For sqlite-vec: pip install sqlite-vec\n"
                            f"  • For sqlite-vss: pip install sqlite-vss\n"
                            f"Or set vector_extension='none' to suppress this warning."
                        )
                else:
                    logging.info("Using pure Python fallback mode for vector operations")
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_source_id ON chunks(source_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_source_index ON chunks(source_id, chunk_index)")
            
            # Add chunk_count column to sources table if it doesn't exist (for backwards compatibility)
            try:
                conn.execute("ALTER TABLE sources ADD COLUMN chunk_count INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                # Column already exists
                pass
            
            # Add loader_type column to sources table if it doesn't exist (for backwards compatibility)
            try:
                conn.execute("ALTER TABLE sources ADD COLUMN loader_type TEXT")
            except sqlite3.OperationalError:
                # Column already exists
                pass
            
            # Add git_commit column to sources table if it doesn't exist (for backwards compatibility)
            try:
                conn.execute("ALTER TABLE sources ADD COLUMN git_commit TEXT")
            except sqlite3.OperationalError:
                # Column already exists
                pass
            
            # Add embedding_dimensions column to chunks table if it doesn't exist (for backwards compatibility)
            try:
                conn.execute("ALTER TABLE chunks ADD COLUMN embedding_dimensions INTEGER")
            except sqlite3.OperationalError:
                # Column already exists
                pass
            
            conn.commit()
    
    def _try_load_extension(self, conn: sqlite3.Connection) -> None:
        """Try to load SQLite vector extension based on user preference."""
        # If user explicitly wants no extension, use fallback
        if self.vector_extension == "none":
            self._fallback_reason = "disabled by user configuration (vector_extension='none')"
            return
        
        # Determine which extensions to try based on user preference
        if self.vector_extension == "sqlite-vec":
            extensions_to_try = ["vec"]
            required = True
        elif self.vector_extension == "sqlite-vss":
            extensions_to_try = ["vss"]
            required = True
        else:  # "auto"
            # Try sqlite-vec first (preferred), then sqlite-vss
            extensions_to_try = ["vec", "vss"]
            required = False
        
        # Try to load extensions
        for ext_name in extensions_to_try:
            try:
                conn.enable_load_extension(True)
                conn.load_extension(ext_name)
                self._extension_name = ext_name
                self._extension_available = True
                return
            except (sqlite3.OperationalError, AttributeError) as e:
                if required:
                    # If this extension was explicitly required, fail with clear error
                    if isinstance(e, AttributeError):
                        raise SqliteExtensionUnavailableError(
                            f"Required vector extension '{ext_name}' could not be loaded: "
                            f"SQLite was compiled without extension support (enable_load_extension not available). "
                            f"Rebuild SQLite with extension support or use vector_extension='none' for pure Python mode."
                        )
                    else:
                        raise SqliteExtensionUnavailableError(
                            f"Required vector extension '{ext_name}' could not be loaded: {e}. "
                            f"Install the extension or use vector_extension='none' for pure Python mode."
                        )
                # Continue trying other extensions in auto mode
                continue
        
        # If we get here and no extension could be loaded
        if required:
            # This should not happen as we would have raised above
            raise SqliteExtensionUnavailableError(
                f"Required vector extension could not be loaded."
            )
        else:
            # Auto mode - all extensions failed, use fallback
            self._fallback_reason = f"none of the tried extensions ({', '.join(extensions_to_try)}) are available"
            self._extension_name = None
            self._extension_available = False
    
    def _create_extension_tables(self, conn: sqlite3.Connection) -> None:
        """Create tables using SQLite vector extension."""
        if self._extension_name == "vec":
            # sqlite-vec extension
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS chunk_embeddings USING vec0(
                    chunk_id TEXT PRIMARY KEY,
                    embedding FLOAT[{dim}]
                )
            """.format(dim=self.embedding_dimension))
        else:
            # sqlite-vss extension
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS chunk_embeddings USING vss0(
                    embedding({dim})
                )
            """.format(dim=self.embedding_dimension))
    
    def _create_fallback_tables(self, conn: sqlite3.Connection) -> None:
        """Create tables for fallback mode (no extension)."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chunk_embeddings (
                chunk_id TEXT PRIMARY KEY,
                embedding BLOB NOT NULL,
                embedding_norm REAL NOT NULL,
                FOREIGN KEY (chunk_id) REFERENCES chunks (chunk_id) ON DELETE CASCADE
            )
        """)
        
        conn.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_norm ON chunk_embeddings(embedding_norm)")
    
    def upsert_source(self, source) -> None:
        """Insert or update a source record."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sources 
                (source_id, path, file_size, mime_type, loader_type, git_commit, mtime, sha256_hash, indexed_at, chunk_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source.source_id,
                str(source.path),
                source.file_size,
                source.mime_type,
                source.loader_type,
                source.git_commit,
                source.mtime.timestamp(),
                source.sha256_hash,
                source.indexed_at.timestamp(),
                source.chunk_count,
            ))
            conn.commit()
    
    def upsert_chunk(self, chunk: Chunk) -> None:
        """Insert or update a chunk record."""
        with self._get_connection() as conn:
            # Validate embedding dimensions if present
            embedding_dimensions = None
            if chunk.embedding:
                embedding_dimensions = len(chunk.embedding)
                if embedding_dimensions != self.embedding_dimension:
                    raise ValueError(f"Embedding dimensions mismatch: expected {self.embedding_dimension}, got {embedding_dimensions}")
            
            # Upsert chunk
            conn.execute("""
                INSERT OR REPLACE INTO chunks 
                (chunk_id, source_id, text, metadata, chunk_index, start_char, end_char, 
                 embedding_model, embedded_at, embedding_dimensions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chunk.chunk_id,
                chunk.source_id,
                chunk.text,
                json.dumps(chunk.metadata) if chunk.metadata else None,
                chunk.chunk_index,
                chunk.start_char,
                chunk.end_char,
                chunk.embedding_model,
                chunk.embedded_at.timestamp() if chunk.embedded_at else None,
                embedding_dimensions,
            ))
            
            # Upsert embedding if available
            if chunk.embedding:
                self._upsert_embedding(conn, chunk)
            
            conn.commit()
    
    def _upsert_embedding(self, conn: sqlite3.Connection, chunk: Chunk) -> None:
        """Upsert embedding using appropriate method."""
        if self._extension_available:
            self._upsert_embedding_extension(conn, chunk)
        else:
            self._upsert_embedding_fallback(conn, chunk)
    
    def _upsert_embedding_extension(self, conn: sqlite3.Connection, chunk: Chunk) -> None:
        """Upsert embedding using SQLite extension."""
        if self._extension_name == "vec":
            conn.execute("""
                INSERT OR REPLACE INTO chunk_embeddings (chunk_id, embedding)
                VALUES (?, ?)
            """, (chunk.chunk_id, chunk.embedding))
        else:
            # vss extension
            conn.execute("""
                INSERT OR REPLACE INTO chunk_embeddings (rowid, embedding)
                VALUES ((SELECT rowid FROM chunks WHERE chunk_id = ?), ?)
            """, (chunk.chunk_id, chunk.embedding))
    
    def _upsert_embedding_fallback(self, conn: sqlite3.Connection, chunk: Chunk) -> None:
        """Upsert embedding in fallback mode."""
        if chunk.embedding:
            if HAS_NUMPY:
                # Use numpy for optimized conversion
                embedding_array = np.array(chunk.embedding, dtype=np.float32)
                embedding_blob = embedding_array.tobytes()
            else:
                # Pure Python fallback
                embedding_blob = self._floats_to_bytes(chunk.embedding)
            
            conn.execute("""
                UPDATE chunks SET embedding = ? WHERE chunk_id = ?
            """, (embedding_blob, chunk.chunk_id))
    
    def get_existing_sources(self) -> List[str]:
        """Get list of existing source IDs."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT source_id FROM sources")
            return [row[0] for row in cursor.fetchall()]
    
    def get_source_hash(self, source_id: str) -> Optional[str]:
        """Get the SHA256 hash for a source."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT sha256_hash FROM sources WHERE source_id = ?",
                (source_id,)
            )
            row = cursor.fetchone()
            return row[0] if row else None
    
    def get_source(self, source_id: str) -> Optional[Source]:
        """Get a source by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT source_id, path, file_size, mime_type, loader_type, git_commit,
                       mtime, sha256_hash, indexed_at, chunk_count
                FROM sources 
                WHERE source_id = ?
            """, (source_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            from datetime import datetime
            return Source(
                source_id=row[0],
                path=Path(row[1]),
                file_size=row[2],
                mime_type=row[3],
                loader_type=row[4],
                git_commit=row[5],
                mtime=datetime.fromtimestamp(row[6]),
                sha256_hash=row[7],
                indexed_at=datetime.fromtimestamp(row[8]),
                chunk_count=row[9] or 0,
            )
    
    def delete_chunks_for_source(self, source_id: str) -> None:
        """Delete all chunks for a source but keep the source record."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM chunks WHERE source_id = ?", (source_id,))
            conn.commit()
    
    def delete_source(self, source_id: str) -> None:
        """Delete a source and all its chunks."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM chunks WHERE source_id = ?", (source_id,))
            conn.execute("DELETE FROM sources WHERE source_id = ?", (source_id,))
            conn.commit()
    
    def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        similarity_threshold: float = 0.0,
    ) -> List[Tuple[str, float]]:
        """
        Search for chunks similar to the given embedding.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            List of (chunk_id, similarity_score) tuples
        """
        # Validate query embedding dimensions
        if len(query_embedding) != self.embedding_dimension:
            raise ValueError(f"Query embedding dimensions mismatch: expected {self.embedding_dimension}, got {len(query_embedding)}")
        
        if self._extension_available:
            return self._search_extension(query_embedding, top_k, similarity_threshold)
        else:
            return self._search_fallback(query_embedding, top_k, similarity_threshold)
    
    def _search_extension(
        self,
        query_embedding: List[float],
        top_k: int,
        similarity_threshold: float,
    ) -> List[Tuple[str, float]]:
        """Search using SQLite extension."""
        with self._get_connection() as conn:
            if self._extension_name == "vec":
                # sqlite-vec KNN search
                cursor = conn.execute("""
                    SELECT chunk_id, distance
                    FROM chunk_embeddings
                    WHERE embedding MATCH ?
                    ORDER BY distance
                    LIMIT ?
                """, (query_embedding, top_k))
            else:
                # sqlite-vss KNN search
                cursor = conn.execute("""
                    SELECT chunk_id, distance
                    FROM chunk_embeddings
                    WHERE vss_search(embedding, ?)
                    ORDER BY distance
                    LIMIT ?
                """, (query_embedding, top_k))
            
            results = []
            for row in cursor.fetchall():
                chunk_id, distance = row
                # Convert distance to similarity (assuming cosine distance)
                similarity = 1.0 - distance
                if similarity >= similarity_threshold:
                    results.append((chunk_id, similarity))
            
            return results
    
    def _search_fallback(
        self,
        query_embedding: List[float],
        top_k: int,
        similarity_threshold: float,
    ) -> List[Tuple[str, float]]:
        """Search using fallback cosine similarity."""
        if HAS_NUMPY:
            # Use numpy for optimized operations
            query_array = np.array(query_embedding, dtype=np.float32)
            query_norm = np.linalg.norm(query_array)
            
            if query_norm == 0:
                return []
            
            query_normalized = query_array / query_norm
        else:
            # Pure Python fallback
            query_norm = sum(x * x for x in query_embedding) ** 0.5
            if query_norm == 0:
                return []
            query_normalized = [x / query_norm for x in query_embedding]
        
        with self._get_connection() as conn:
            # Get all chunks with embeddings
            cursor = conn.execute("""
                SELECT chunk_id, embedding
                FROM chunks
                WHERE embedding IS NOT NULL
            """)
            
            results = []
            for row in cursor.fetchall():
                chunk_id, embedding_blob = row
                
                # Decode embedding
                if HAS_NUMPY:
                    embedding_array = np.frombuffer(embedding_blob, dtype=np.float32)
                    embedding_norm = np.linalg.norm(embedding_array)
                    if embedding_norm > 0:
                        embedding_normalized = embedding_array / embedding_norm
                        similarity = float(np.dot(query_normalized, embedding_normalized))
                else:
                    embedding_list = self._bytes_to_floats(embedding_blob)
                    embedding_norm = sum(x * x for x in embedding_list) ** 0.5
                    if embedding_norm > 0:
                        embedding_normalized = [x / embedding_norm for x in embedding_list]
                        similarity = self._cosine_similarity(query_embedding, embedding_list)
                
                if similarity >= similarity_threshold:
                    results.append((chunk_id, similarity))
            
            # Sort by similarity and return top_k
            return sorted(results, key=lambda x: x[1], reverse=True)[:top_k]
                
    def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """Get a chunk by ID."""
        with self._get_connection() as conn:
            if self._extension_available:
                # Get chunk without embedding (embedding is in separate table)
                cursor = conn.execute("""
                    SELECT chunk_id, source_id, text, metadata, chunk_index, start_char, end_char,
                           embedding_model, embedded_at, embedding_dimensions
                    FROM chunks WHERE chunk_id = ?
                """, (chunk_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Get embedding from extension table
                embedding = None
                if self._extension_name == "vec":
                    cursor = conn.execute("""
                        SELECT embedding FROM chunk_embeddings WHERE chunk_id = ?
                    """, (chunk_id,))
                else:  # vss
                    cursor = conn.execute("""
                        SELECT embedding FROM chunk_embeddings 
                        WHERE rowid = (SELECT rowid FROM chunks WHERE chunk_id = ?)
                    """, (chunk_id,))
                
                embedding_row = cursor.fetchone()
                if embedding_row:
                    embedding = list(embedding_row[0])
            else:
                # Get chunk with embedding from fallback mode
                cursor = conn.execute("""
                    SELECT chunk_id, source_id, text, metadata, chunk_index, start_char, end_char,
                           embedding_model, embedded_at, embedding_dimensions, embedding
                    FROM chunks WHERE chunk_id = ?
                """, (chunk_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Decode embedding from BLOB
                embedding = None
                if row[10]:  # embedding column
                    if HAS_NUMPY:
                        import numpy as np
                        embedding = list(np.frombuffer(row[10], dtype=np.float32))
                    else:
                        embedding = self._bytes_to_floats(row[10])
            
            import json
            metadata = json.loads(row[3]) if row[3] else {}
            embedded_at = datetime.fromtimestamp(row[8]) if row[8] else None
            embedding_dimensions = row[9] if len(row) > 9 else None
            
            return Chunk(
                chunk_id=row[0],
                source_id=row[1],
                text=row[2],
                metadata=metadata,
                chunk_index=row[4],
                start_char=row[5],
                end_char=row[6],
                embedding_model=row[7],
                embedded_at=embedded_at,
                embedding_dimensions=embedding_dimensions,
                embedding=embedding,
            )
    
    def get_source_chunks(self, source_id: str) -> List[Chunk]:
        """Get all chunks for a source."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT chunk_id, source_id, text, metadata, chunk_index, start_char, end_char,
                       embedding_model, embedded_at, embedding_dimensions
                FROM chunks WHERE source_id = ?
                ORDER BY chunk_index
            """, (source_id,))
            
            chunks = []
            for row in cursor.fetchall():
                import json
                metadata = json.loads(row[3]) if row[3] else {}
                embedded_at = datetime.fromtimestamp(row[8]) if row[8] else None
                embedding_dimensions = row[9] if len(row) > 9 else None
                
                chunk = Chunk(
                    chunk_id=row[0],
                    source_id=row[1],
                    text=row[2],
                    metadata=metadata,
                    chunk_index=row[4],
                    start_char=row[5],
                    end_char=row[6],
                    embedding_model=row[7],
                    embedded_at=embedded_at,
                    embedding_dimensions=embedding_dimensions,
                )
                chunks.append(chunk)
            
            return chunks
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self._get_connection() as conn:
            stats = {}
            
            # Source stats
            cursor = conn.execute("SELECT COUNT(*) FROM sources")
            stats['sources_count'] = cursor.fetchone()[0]
            
            # Chunk stats
            cursor = conn.execute("SELECT COUNT(*) FROM chunks")
            stats['chunks_count'] = cursor.fetchone()[0]
            
            # Embedding stats
            if self._extension_available:
                cursor = conn.execute("SELECT COUNT(*) FROM chunk_embeddings")
                stats['embeddings_count'] = cursor.fetchone()[0]
            else:
                cursor = conn.execute("SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL")
                stats['embeddings_count'] = cursor.fetchone()[0]
            
            # Extension info
            stats['extension_available'] = self._extension_available
            stats['extension_name'] = self._extension_name if self._extension_available else None
            stats['fallback_reason'] = self._fallback_reason
            
            # Database size
            if self.db_path.exists():
                stats['db_size_bytes'] = self.db_path.stat().st_size
            else:
                stats['db_size_bytes'] = 0
            
            return stats
    
    def _floats_to_bytes(self, floats: List[float]) -> bytes:
        """Convert list of floats to bytes (pure Python fallback)."""
        return struct.pack('f' * len(floats), *floats)
    
    def _bytes_to_floats(self, b: bytes) -> List[float]:
        """Convert bytes to list of floats (pure Python fallback)."""
        return list(struct.unpack('f' * (len(b) // 4), b))
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors (pure Python fallback)."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def close(self) -> None:
        """Close database connections."""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            delattr(self._local, 'connection')
