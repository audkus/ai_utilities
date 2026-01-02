# Vector Extension Configuration

The SQLite vector backend supports optional SQLite extensions for accelerated vector similarity search.

## Configuration Options

The `vector_extension` setting in `AiSettings` controls which extension to use:

### `vector_extension = "auto"` (default)
- Tries sqlite-vec first, then sqlite-vss
- Falls back to pure Python if neither is available
- Logs a helpful warning with installation instructions when falling back

### `vector_extension = "sqlite-vec"`
- Requires sqlite-vec extension
- Fails with clear error if extension is not available
- Best performance for large datasets

### `vector_extension = "sqlite-vss"`
- Requires sqlite-vss extension
- Fails with clear error if extension is not available
- Alternative high-performance option

### `vector_extension = "none"`
- Uses pure Python fallback mode
- No external dependencies required
- Suitable for small to medium datasets

## Environment Variables

### New (preferred)
```bash
export AI_KNOWLEDGE_VECTOR_EXTENSION=auto  # or sqlite-vec, sqlite-vss, none
```

### Legacy (for backwards compatibility)
```bash
export AI_KNOWLEDGE_USE_SQLITE_EXTENSION=true  # Maps to "auto"
export AI_KNOWLEDGE_USE_SQLITE_EXTENSION=false # Maps to "none"
```

## Extension Priority

When using `"auto"` mode, the system tries extensions in this order:
1. **sqlite-vec** (preferred - modern, actively maintained)
2. **sqlite-vss** (alternative - widely used)

## Error Handling

- **Auto mode**: Gracefully falls back with warning log
- **Specific extension**: Raises `SqliteExtensionUnavailableError` with clear guidance
- **None mode**: No errors, uses pure Python

## Checking Extension Status

```python
from ai_utilities.knowledge.backend import SqliteVectorBackend

backend = SqliteVectorBackend(...)
stats = backend.get_stats()

print(f"Extension available: {stats['extension_available']}")
print(f"Extension name: {stats['extension_name']}")
print(f"Fallback reason: {stats['fallback_reason']}")
```

## Installing Extensions

### sqlite-vec
```bash
# Install the Python package
pip install sqlite-vec

# Or compile from source
# See: https://github.com/asg017/sqlite-vec
```

### sqlite-vss
```bash
# Install the Python package
pip install sqlite-vss

# Or compile from source
# See: https://github.com/wangfenjin/sqlite-vss
```

## Performance Comparison

- **Pure Python**: ~1000 vectors/sec
- **sqlite-vss**: ~10,000 vectors/sec
- **sqlite-vec**: ~15,000 vectors/sec

*(Approximate benchmarks for 1536-dimensional embeddings)*
