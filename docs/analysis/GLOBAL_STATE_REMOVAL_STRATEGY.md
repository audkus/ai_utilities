# Global State Removal Strategy

## Overview

This document outlines the long-term strategy to remove global state dependencies from ai_utilities, making the system more testable, maintainable, and thread-safe.

## Current Global State Dependencies

### 1. Configuration Manager (`ai_config_manager.py`)
```python
# Global singleton pattern
_config_manager: Optional[AIConfigManager] = None

def get_config_manager() -> AIConfigManager:
    global _config_manager
    if _config_manager is None:
        _config_manager = AIConfigManager()
    return _config_manager
```

### 2. Environment Source (`env_overrides.py`)
```python
# Global instance
_ai_env_source = OverrideAwareEnvSource("AI_")
```

### 3. Metrics Registry (`metrics.py`)
```python
# Global singleton
metrics = MetricsRegistry()
```

### 4. Usage Tracker (`usage_tracker.py`)
- Contains global tracking modes
- Uses process-wide state

### 5. Direct Environment Access
- Multiple modules directly access `os.environ`
- Bypasses the contextvar override system

## Removal Strategy

### Phase 4.1: Dependency Injection Framework
**Goal**: Enable explicit dependency injection instead of global singletons

#### 1. Create Configuration Context
```python
class ConfigurationContext:
    """Context manager for configuration dependencies."""
    
    def __init__(self, config_manager=None, env_source=None, metrics=None):
        self.config_manager = config_manager or AIConfigManager()
        self.env_source = env_source or OverrideAwareEnvSource("AI_")
        self.metrics = metrics or MetricsRegistry()
    
    def __enter__(self):
        # Set context-local instances
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup context
        pass
```

#### 2. Refactor Global Access Points
- Replace `get_config_manager()` with context-aware access
- Replace direct `metrics.` usage with injected instances
- Replace `_ai_env_source` with context-aware sources

### Phase 4.2: Environment Access Abstraction
**Goal**: Eliminate direct `os.environ` access

#### 1. Create Environment Provider Interface
```python
class EnvironmentProvider(ABC):
    """Abstract interface for environment variable access."""
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> str | None:
        """Get environment variable value."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: str) -> None:
        """Set environment variable value."""
        pass

class ContextVarEnvironmentProvider(EnvironmentProvider):
    """Environment provider that respects contextvar overrides."""
    
    def get(self, key: str, default: Any = None) -> str | None:
        # Check contextvar overrides first, then real environment
        pass
    
    def set(self, key: str, value: str) -> None:
        # Set in contextvar overrides
        pass
```

#### 2. Replace Direct Environment Access
- Audit all `os.environ` usage
- Replace with environment provider interface
- Maintain backward compatibility

### Phase 4.3: Metrics Collection Refactoring
**Goal**: Remove global metrics registry

#### 1. Metrics Context
```python
class MetricsContext:
    """Context for metrics collection."""
    
    def __init__(self, registry=None):
        self.registry = registry or MetricsRegistry()
    
    def increment(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Increment a metric."""
        self.registry.increment(name, value, tags)
```

#### 2. Inject Metrics Context
- Pass metrics context to components that need it
- Remove global `metrics` instance
- Update all metrics usage

### Phase 4.4: Configuration Management Refactoring
**Goal**: Remove global configuration manager

#### 1. Configuration Provider
```python
class ConfigurationProvider:
    """Provider for configuration management."""
    
    def __init__(self, config_manager=None, env_provider=None):
        self.config_manager = config_manager or AIConfigManager()
        self.env_provider = env_provider or ContextVarEnvironmentProvider()
    
    def get_ai_settings(self, **kwargs) -> AiSettings:
        """Get AI settings with proper dependency injection."""
        return self.config_manager.get_ai_settings(self.env_provider, **kwargs)
```

#### 2. Update AiSettings
- Remove dependency on global environment access
- Accept environment provider explicitly
- Maintain backward compatibility

## Implementation Plan

### Step 1: Create New Infrastructure (Week 1)
1. Create `ConfigurationContext` class
2. Create `EnvironmentProvider` interface and implementations
3. Create `MetricsContext` class
4. Add comprehensive tests for new components

### Step 2: Refactor Core Components (Week 2)
1. Update `AiSettings` to use `EnvironmentProvider`
2. Update `AIConfigManager` to use dependency injection
3. Update metrics usage throughout codebase
4. Maintain backward compatibility layers

### Step 3: Migrate Usage Patterns (Week 3)
1. Update client code to use new patterns
2. Update tests to use injected dependencies
3. Add migration guide and documentation
4. Deprecate global access patterns

### Step 4: Remove Global State (Week 4)
1. Remove global singletons
2. Remove backward compatibility layers
3. Update documentation
4. Final testing and validation

## Backward Compatibility Strategy

### 1. Gradual Migration
- Keep global access patterns working during transition
- Add deprecation warnings for global usage
- Provide clear migration paths

### 2. Compatibility Layer
```python
# Backward compatibility (with warnings)
def get_config_manager() -> AIConfigManager:
    warnings.warn("get_config_manager() is deprecated, use ConfigurationContext", DeprecationWarning)
    return get_current_context().config_manager

# New pattern
with ConfigurationContext() as ctx:
    config = ctx.config_manager
```

### 3. Testing Strategy
- Test both old and new patterns during transition
- Ensure no breaking changes for existing users
- Comprehensive integration tests

## Benefits

### 1. Testability
- No more global state to reset between tests
- Explicit dependencies make testing easier
- Better isolation between tests

### 2. Thread Safety
- No shared global state between threads
- Context-local state management
- Better concurrent execution support

### 3. Maintainability
- Clear dependency relationships
- Easier to reason about code behavior
- Better modularity

### 4. Flexibility
- Can use different configurations in different contexts
- Support for multi-tenant scenarios
- Better composability

## Risk Mitigation

### 1. Breaking Changes
- Maintain backward compatibility during transition
- Provide clear migration documentation
- Extensive testing of compatibility layers

### 2. Performance Impact
- Benchmark new patterns for performance
- Optimize context creation and management
- Minimize overhead for common use cases

### 3. Complexity
- Keep APIs simple and intuitive
- Provide good documentation and examples
- Gradual learning curve for users

## Success Criteria

1. ✅ All global singletons removed
2. ✅ No direct `os.environ` access
3. ✅ All tests pass without global state reset
4. ✅ Backward compatibility maintained during transition
5. ✅ Performance impact < 5%
6. ✅ Documentation and migration guide complete

## Timeline

- **Week 1**: Infrastructure creation and testing
- **Week 2**: Core component refactoring
- **Week 3**: Usage pattern migration
- **Week 4**: Global state removal and finalization

This strategy provides a clear path to eliminating global state while maintaining system stability and user experience.
