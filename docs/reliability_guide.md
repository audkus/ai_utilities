# Reliability and Maintenance Guide

This guide covers best practices for deploying, maintaining, and troubleshooting AI Utilities in production environments.

## 🏗️ Production Deployment

### Environment Configuration

#### 1. API Key Management
```bash
# Production environment variables
export AI_API_KEY="your-production-api-key"
export AI_MODEL="gpt-4"  # Use specific model, not test defaults
export AI_TEMPERATURE="0.7"
export AI_TIMEOUT="60"
export AI_CACHE_ENABLED="true"
export AI_CACHE_BACKEND="sqlite"
export AI_CACHE_SQLITE_PATH="/var/cache/ai_utilities/cache.sqlite"
```

#### 2. Rate Limiting Configuration
```python
from ai_utilities import AiSettings

# Production settings with conservative limits
settings = AiSettings(
    api_key="your-key",
    model="gpt-4",
    temperature=0.7,
    timeout=60,
    # Enable caching for cost control
    cache_enabled=True,
    cache_backend="sqlite",
    cache_ttl_s=3600,  # 1 hour cache
    cache_max_temperature=0.8,  # Only cache deterministic responses
    # Usage tracking for monitoring
    usage_scope="global",  # Track across all instances
    usage_client_id="production-server-1"
)
```

### High Availability Setup

#### 1. Multiple Provider Configuration
```python
# Fallback configuration for high availability
primary_settings = AiSettings(
    provider="openai",
    api_key="openai-key",
    model="gpt-4"
)

fallback_settings = AiSettings(
    provider="openai_compatible",
    base_url="https://api.deepseek.com/v1",
    api_key="deepseek-key",
    model="deepseek-chat"
)

# Implement provider switching logic
def get_client():
    try:
        return AiClient(primary_settings)
    except Exception as e:
        logger.warning(f"Primary provider failed: {e}, using fallback")
        return AiClient(fallback_settings)
```

#### 2. Circuit Breaker Pattern
```python
import time
from functools import wraps

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = "HALF_OPEN"
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                raise e
        return wrapper

# Usage
@circuit_breaker(failure_threshold=3, timeout=30)
def call_ai_with_circuit_breaker(client, prompt):
    return client.ask(prompt)
```

## 🔍 Monitoring and Observability

### 1. Usage Tracking
```python
from ai_utilities import AiClient, AiSettings

# Configure global usage tracking
settings = AiSettings(
    usage_scope="global",
    usage_client_id="production-server-1"
)

client = AiClient(settings)

# Monitor usage statistics
def monitor_usage():
    stats = client.get_usage_stats()
    if stats:
        print(f"Total requests: {stats.total_requests}")
        print(f"Total tokens: {stats.total_tokens}")
        print(f"Estimated cost: ${stats.estimated_cost:.2f}")
        
        # Alert on high usage
        if stats.total_tokens > 1000000:  # 1M tokens
            send_alert("High token usage detected")
```

### 2. Health Checks
```python
def health_check():
    """Comprehensive health check for AI Utilities."""
    try:
        # Test basic functionality
        settings = AiSettings(api_key="test-key")
        client = AiClient(settings)
        
        # Test cache connectivity
        if settings.cache_enabled:
            client.cache.get("health_check_key")
        
        # Test provider connectivity (if configured)
        if hasattr(client, 'provider') and client.provider:
            # This will fail if provider is unreachable
            pass
        
        return {"status": "healthy", "timestamp": time.time()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "timestamp": time.time()}

# Flask health check endpoint
@app.route('/health')
def health_endpoint():
    return jsonify(health_check())
```

### 3. Logging Configuration
```python
import logging

# Configure AI Utilities logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_utilities")

# Add custom handlers for production
import sys
from logging.handlers import RotatingFileHandler

# File handler for persistent logs
file_handler = RotatingFileHandler(
    '/var/log/ai_utilities/app.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)

# Structured logging for monitoring
import json
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName
        }
        return json.dumps(log_entry)

json_handler = logging.StreamHandler(sys.stdout)
json_handler.setFormatter(JSONFormatter())

logger.addHandler(file_handler)
logger.addHandler(json_handler)
```

## 🛠️ Maintenance Operations

### 1. Cache Management
```python
from ai_utilities.cache import SqliteCache
import sqlite3
from pathlib import Path

def maintain_cache():
    """Perform cache maintenance operations."""
    cache_path = Path("/var/cache/ai_utilities/cache.sqlite")
    
    if cache_path.exists():
        # Get cache statistics
        conn = sqlite3.connect(cache_path)
        cursor = conn.cursor()
        
        # Total entries
        cursor.execute("SELECT COUNT(*) FROM ai_cache")
        total_entries = cursor.fetchone()[0]
        
        # Old entries (older than 7 days)
        cursor.execute("""
            SELECT COUNT(*) FROM ai_cache 
            WHERE created_at < datetime('now', '-7 days')
        """)
        old_entries = cursor.fetchone()[0]
        
        print(f"Cache stats: {total_entries} total, {old_entries} old")
        
        # Clean up old entries
        if old_entries > 1000:
            cursor.execute("""
                DELETE FROM ai_cache 
                WHERE created_at < datetime('now', '-7 days')
            """)
            conn.commit()
            print(f"Cleaned up {cursor.rowcount} old cache entries")
        
        conn.close()

# Schedule regular maintenance (e.g., daily)
import schedule
schedule.every().day.at("02:00").do(maintain_cache)
```

### 2. Configuration Updates
```python
def reload_configuration():
    """Hot-reload configuration without restart."""
    try:
        # Reload from environment or config file
        new_settings = AiSettings()
        
        # Validate new settings
        if new_settings.api_key and new_settings.model:
            # Apply to existing client
            global client
            client.settings = new_settings
            logger.info("Configuration reloaded successfully")
        else:
            logger.error("Invalid configuration after reload")
    except Exception as e:
        logger.error(f"Failed to reload configuration: {e}")

# Signal handler for graceful reload
import signal
def handle_reload_signal(signum, frame):
    logger.info("Received reload signal, updating configuration...")
    reload_configuration()

signal.signal(signal.SIGHUP, handle_reload_signal)
```

### 3. Performance Optimization
```python
def optimize_performance():
    """Apply performance optimizations."""
    # Pre-warm connections
    client = AiClient()
    
    # Warm up cache with common queries
    common_queries = [
        "Summarize this text:",
        "Translate to English:",
        "Explain this concept:"
    ]
    
    for query in common_queries:
        try:
            client.ask(query, temperature=0)  # Deterministic for caching
        except Exception as e:
            logger.warning(f"Cache warm-up failed for '{query}': {e}")
    
    logger.info("Performance optimization completed")

# Run on startup
optimize_performance()
```

## 🚨 Troubleshooting Common Issues

### 1. Memory Leaks
```python
import psutil
import gc

def monitor_memory():
    """Monitor memory usage and detect leaks."""
    process = psutil.Process()
    memory_info = process.memory_info()
    
    print(f"RSS: {memory_info.rss / 1024 / 1024:.2f} MB")
    print(f"VMS: {memory_info.vms / 1024 / 1024:.2f} MB")
    
    # Force garbage collection if memory is high
    if memory_info.rss > 1024 * 1024 * 1024:  # 1GB
        gc.collect()
        logger.warning("Forced garbage collection due to high memory usage")

# Schedule memory monitoring
schedule.every(5).minutes.do(monitor_memory)
```

### 2. Cache Corruption
```python
def repair_cache():
    """Detect and repair cache corruption."""
    cache_path = Path("/var/cache/ai_utilities/cache.sqlite")
    
    try:
        # Test cache integrity
        cache = SqliteCache(cache_path)
        cache.get("test_key")  # Test operation
        
    except sqlite3.DatabaseError:
        logger.error("Cache corruption detected, rebuilding...")
        
        # Backup corrupted cache
        backup_path = cache_path.with_suffix('.sqlite.corrupted')
        cache_path.rename(backup_path)
        
        # Create new cache
        cache = SqliteCache(cache_path)
        logger.info("Cache rebuilt successfully")
```

### 3. Provider Failover
```python
def handle_provider_failure(error):
    """Graceful handling of provider failures."""
    logger.error(f"Provider failure: {error}")
    
    # Implement exponential backoff
    retry_delay = min(300, 2 ** attempt_number)  # Max 5 minutes
    
    # Try fallback provider
    try_fallback_provider()
    
    # Alert operations team
    send_alert(f"AI Provider failure: {error}")
    
    # Return cached responses if available
    return get_cached_response_if_available()
```

## 📊 Performance Metrics

### Key Performance Indicators
- **Response Time**: Average time per request
- **Cache Hit Rate**: Percentage of requests served from cache
- **Error Rate**: Percentage of failed requests
- **Token Usage**: Total tokens consumed
- **Cost Efficiency**: Cost per successful request

### Monitoring Dashboard
```python
def get_metrics():
    """Collect performance metrics for monitoring."""
    stats = client.get_usage_stats()
    
    metrics = {
        'timestamp': time.time(),
        'total_requests': stats.total_requests if stats else 0,
        'total_tokens': stats.total_tokens if stats else 0,
        'estimated_cost': stats.estimated_cost if stats else 0,
        'cache_hit_rate': calculate_cache_hit_rate(),
        'average_response_time': calculate_average_response_time(),
        'error_rate': calculate_error_rate()
    }
    
    return metrics

# Export to monitoring system (Prometheus, DataDog, etc.)
def export_metrics():
    metrics = get_metrics()
    # Send to your monitoring system
    monitoring_client.export(metrics)
```

## 🔒 Security Considerations

### 1. API Key Rotation
```python
import keyring
from datetime import datetime, timedelta

def rotate_api_keys():
    """Automated API key rotation."""
    current_key = get_current_api_key()
    
    # Check if key needs rotation (e.g., every 90 days)
    if key_age_days(current_key) > 90:
        new_key = generate_new_api_key()
        store_api_key(new_key)
        logger.info("API key rotated successfully")
```

### 2. Audit Logging
```python
def audit_log_usage(client, prompt, response):
    """Log all AI interactions for audit purposes."""
    audit_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': get_current_user(),
        'prompt_hash': hash_prompt(prompt),
        'response_length': len(response),
        'model_used': client.settings.model,
        'tokens_estimated': estimate_tokens(prompt + response)
    }
    
    # Write to audit log
    with open('/var/log/ai_utilities/audit.log', 'a') as f:
        f.write(json.dumps(audit_entry) + '\n')
```

This guide provides comprehensive coverage of production deployment, monitoring, maintenance, and troubleshooting for AI Utilities. Follow these practices to ensure reliable, maintainable deployments in production environments.
