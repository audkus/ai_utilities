# Smart Caching

## What is Caching?

Caching is the practice of storing AI responses locally so that when you ask the same question again, you get an instant answer without making another API call. This provides three key benefits:

1. **Cost Savings** - Avoid paying for identical API requests
2. **Speed** - Cached responses are instant (no network latency)
3. **Reliability** - Works even when APIs are unavailable

## How It Works

```python
# First time you ask:
response = client.ask("What is Python?")
# → Hits OpenAI API, costs ~0.001 USD, takes 1-2 seconds

# Second time you ask (same question):
response = client.ask("What is Python?")  
# → Returns cached response instantly, $0 cost, ~0ms
```

## Quick Start

### Enable Caching

```python
from ai_utilities import AiClient, AiSettings

# Enable memory caching
settings = AiSettings(
    cache_enabled=True,
    cache_backend="memory",
    cache_ttl_s=3600  # 1 hour
)

client = AiClient(settings)

# First call hits API and caches response
response1 = client.ask("Explain photosynthesis")

# Second call returns cached response instantly
response2 = client.ask("Explain photosynthesis")
```

### Environment Configuration

```bash
# Enable caching via environment
AI_CACHE_ENABLED=true
AI_CACHE_BACKEND=sqlite
AI_CACHE_TTL_S=3600
```

## Cache Backends

### Memory Cache

**Use for:** Short-lived processes, testing, development

```python
settings = AiSettings(
    cache_enabled=True,
    cache_backend="memory",
    cache_ttl_s=1800  # 30 minutes
)
```

**Pros:** Fast, no setup required
**Cons:** Lost when process ends

### SQLite Cache

**Use for:** Production, persistent caching

```python
from pathlib import Path

settings = AiSettings(
    cache_enabled=True,
    cache_backend="sqlite",
    cache_sqlite_path=Path.home() / ".ai_utilities" / "cache.sqlite",
    cache_ttl_s=3600,  # 1 hour
    cache_sqlite_max_entries=1000
)
```

**Pros:** Persistent, survives restarts
**Cons:** Slightly slower than memory

### Redis Cache

**Use for:** Distributed systems, multiple processes

```python
settings = AiSettings(
    cache_enabled=True,
    cache_backend="redis",
    cache_redis_host="localhost",
    cache_redis_port=6379,
    cache_redis_db=0,
    cache_ttl_s=7200  # 2 hours
)
```

**Pros:** Shared across processes/servers
**Cons:** Requires Redis server

## Cache Namespaces

Namespaces prevent cache pollution between different use cases:

```python
# Learning-related questions
client.ask("What is machine learning?", cache_namespace="learning")
client.ask("Explain neural networks", cache_namespace="learning")

# Work-related questions
client.ask("Write a Python script", cache_namespace="work")
client.ask("Debug this function", cache_namespace="work")

# Same question in different namespace = separate cache entries
client.ask("What is Python?", cache_namespace="learning")
client.ask("What is Python?", cache_namespace="work")
```

## Cache Invalidation

### TTL (Time-To-Live)

Cache entries automatically expire after TTL:

```python
# Cache for 1 hour
settings = AiSettings(cache_ttl_s=3600)

# Cache for 1 day
settings = AiSettings(cache_ttl_s=86400)

# Cache for 1 week
settings = AiSettings(cache_ttl_s=604800)
```

### Manual Cache Clearing

```python
from ai_utilities.cache import get_cache_backend

# Get the cache backend
cache = get_cache_backend(settings)

# Clear all cache
cache.clear()

# Clear specific namespace
cache.clear_namespace("learning")
```

## Performance Impact

### Response Times

- **Cache Hit:** ~1-5ms (instant)
- **Cache Miss:** 500-2000ms (API call)
- **Memory Cache:** ~1ms
- **SQLite Cache:** ~5-10ms
- **Redis Cache:** ~2-5ms

### Cost Savings

Typical savings for repetitive queries:
- **Development:** 80-90% reduction in API calls
- **Production:** 60-80% reduction in API calls
- **Testing:** 95%+ reduction in API calls

## Best Practices

### DO Use Caching For:
- Repetitive questions during development
- Reference data (definitions, explanations)
- Template responses
- Testing and debugging

### DON'T Use Caching For:
- Real-time data (weather, stock prices)
- User-specific sensitive information
- Frequently changing content
- One-off unique queries

### Recommended TTL Settings:
- **Development:** 1-4 hours (frequent changes)
- **Production:** 24 hours (stable content)
- **Reference data:** 1 week (static information)

## Monitoring Cache Performance

```python
# Check cache statistics (if available)
if hasattr(client.cache, 'stats'):
    stats = client.cache.stats()
    print(f"Cache hits: {stats['hits']}")
    print(f"Cache misses: {stats['misses']}")
    print(f"Hit ratio: {stats['hit_ratio']:.2%}")
```

For configuration details, see [Configuration Guide](configuration.md).
