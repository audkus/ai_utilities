"""Tests for dependency injection environment providers."""

import os
import pytest
import warnings

from ai_utilities.di.environment import (
    EnvironmentProvider,
    ContextVarEnvironmentProvider,
    StandardEnvironmentProvider,
    EnvironmentProviderStub,
    get_default_environment_provider,
    set_default_environment_provider,
    get_env,
    get_all_env,
)
from ai_utilities.env_overrides import override_env


class EnvironmentProviderStubImplementation:
    """Test the EnvironmentProvider interface and implementations."""
    
    def test_context_var_provider_basic(self):
        """Test ContextVarEnvironmentProvider basic functionality."""
        provider = ContextVarEnvironmentProvider(warn_on_direct_access=False)
        
        # Test getting environment variable
        result = provider.get("PATH")
        assert result is not None  # PATH should exist
        
        # Test getting non-existent variable
        result = provider.get("NON_EXISTENT_VAR", "default")
        assert result == "default"
    
    def test_context_var_provider_with_overrides(self):
        """Test ContextVarEnvironmentProvider with contextvar overrides."""
        provider = ContextVarEnvironmentProvider(warn_on_direct_access=False)
        
        # Test without override
        result = provider.get("AI_TEST_VAR", "default")
        assert result == "default"
        
        # Test with override
        with override_env({"AI_TEST_VAR": "override_value"}):
            result = provider.get("AI_TEST_VAR", "default")
            assert result == "override_value"
        
        # Test override is cleared
        result = provider.get("AI_TEST_VAR", "default")
        assert result == "default"
    
    def test_context_var_provider_warning(self):
        """Test ContextVarEnvironmentProvider warning in test mode."""
        provider = ContextVarEnvironmentProvider(warn_on_direct_access=True)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # This should generate a warning in test mode
            result = provider.get("PATH")
            
            # Should still return the value but with a warning
            assert result is not None
            assert len(w) > 0
            warning_messages = [str(warning.message) for warning in w]
            assert any("Direct environment access detected" in msg for msg in warning_messages)
    
    def test_standard_provider(self):
        """Test StandardEnvironmentProvider functionality."""
        provider = StandardEnvironmentProvider()
        
        # Test getting environment variable
        result = provider.get("PATH")
        assert result is not None
        
        # Test setting and getting
        provider.set("AI_TEST_VAR", "test_value")
        result = provider.get("AI_TEST_VAR")
        assert result == "test_value"
        
        # Test clearing
        provider.clear("AI_TEST_VAR")
        result = provider.get("AI_TEST_VAR", "default")
        assert result == "default"
        
        # Clean up
        if "AI_TEST_VAR" in os.environ:
            del os.environ["AI_TEST_VAR"]
    
    def test_standard_provider_with_prefix(self):
        """Test StandardEnvironmentProvider with prefix filtering."""
        provider = StandardEnvironmentProvider()
        
        # Set up test variables
        os.environ["AI_TEST_VAR1"] = "value1"
        os.environ["AI_TEST_VAR2"] = "value2"
        os.environ["OTHER_VAR"] = "other_value"
        
        try:
            # Test with prefix
            result = provider.get_all("AI_")
            assert "AI_TEST_VAR1" in result
            assert "AI_TEST_VAR2" in result
            assert "OTHER_VAR" not in result
            
            # Test without prefix
            result = provider.get_all()
            assert "AI_TEST_VAR1" in result
            assert "AI_TEST_VAR2" in result
            assert "OTHER_VAR" in result
        
        finally:
            # Clean up
            for var in ["AI_TEST_VAR1", "AI_TEST_VAR2", "OTHER_VAR"]:
                if var in os.environ:
                    del os.environ[var]
    
    def test_test_provider(self):
        """Test EnvironmentProviderStub functionality."""
        initial_state = {"VAR1": "value1", "VAR2": "value2"}
        provider = EnvironmentProviderStub(initial_state)
        
        # Test getting values
        assert provider.get("VAR1") == "value1"
        assert provider.get("VAR2") == "value2"
        assert provider.get("NON_EXISTENT", "default") == "default"
        
        # Test setting values
        provider.set("VAR3", "value3")
        assert provider.get("VAR3") == "value3"
        
        # Test clearing values
        provider.clear("VAR1")
        assert provider.get("VAR1", "default") == "default"
        assert provider.get("VAR2") == "value2"  # Other values unaffected
        
        # Test reset
        provider.reset({"NEW_VAR": "new_value"})
        assert provider.get("NEW_VAR") == "new_value"
        assert provider.get("VAR1", "default") == "default"
        assert provider.get("VAR2", "default") == "default"
    
    def test_default_provider_management(self):
        """Test default environment provider management."""
        # Test getting default provider
        provider1 = get_default_environment_provider()
        provider2 = get_default_environment_provider()
        assert provider1 is provider2  # Should be same instance
        
        # Test setting default provider
        new_provider = EnvironmentProviderStub()
        set_default_environment_provider(new_provider)
        
        provider3 = get_default_environment_provider()
        assert provider3 is new_provider
        assert provider3 is not provider1
        
        # Test convenience functions use default provider
        result = get_env("NON_EXISTENT", "default")
        assert result == "default"
        
        # Test get_all_env
        all_vars = get_all_env()
        assert isinstance(all_vars, dict)
    
    def test_provider_not_implemented_methods(self):
        """Test that NotImplementedError is raised for unimplemented methods."""
        provider = ContextVarEnvironmentProvider()
        
        # These methods should raise NotImplementedError
        with pytest.raises(NotImplementedError):
            provider.set("TEST_VAR", "value")
        
        with pytest.raises(NotImplementedError):
            provider.clear("TEST_VAR")


class EnvironmentProviderStubIntegration:
    """Integration tests for environment providers."""
    
    def test_context_var_provider_respects_overrides(self):
        """Test that contextvar provider properly respects override_env."""
        provider = ContextVarEnvironmentProvider(warn_on_direct_access=False)
        
        # Set up nested overrides - expect warning for nested override
        with override_env({"AI_VAR1": "outer1", "AI_VAR2": "outer2"}):
            assert provider.get("AI_VAR1") == "outer1"
            assert provider.get("AI_VAR2") == "outer2"
            
            # Nested override should generate warning, but we expect it
            with pytest.warns(UserWarning, match="Nested environment overrides detected"):
                with override_env({"AI_VAR1": "inner1"}):
                    assert provider.get("AI_VAR1") == "inner1"  # Inner override takes precedence
                    assert provider.get("AI_VAR2") == "outer2"  # Outer override still visible
            
            # Back to outer context
            assert provider.get("AI_VAR1") == "outer1"
            assert provider.get("AI_VAR2") == "outer2"
        
        # No overrides
        assert provider.get("AI_VAR1", "default") == "default"
        assert provider.get("AI_VAR2", "default") == "default"
    
    def test_provider_isolation(self):
        """Test that different providers are properly isolated."""
        # Create test provider with specific state
        test_provider = EnvironmentProviderStub({"TEST_VAR": "test_value"})
        
        # Create standard provider
        standard_provider = StandardEnvironmentProvider()
        
        # Set different values
        standard_provider.set("TEST_VAR", "standard_value")
        
        # Each provider should return its own value
        assert test_provider.get("TEST_VAR") == "test_value"
        assert standard_provider.get("TEST_VAR") == "standard_value"
        
        # Clean up
        standard_provider.clear("TEST_VAR")
    
    def test_provider_thread_safety(self):
        """Test that providers work correctly in threaded contexts."""
        import threading
        import time
        
        results = {}
        
        def worker(thread_id):
            """Worker function for threading test."""
            provider = ContextVarEnvironmentProvider(warn_on_direct_access=False)
            
            with override_env({"THREAD_VAR": f"value_{thread_id}"}):
                results[thread_id] = provider.get("THREAD_VAR")
                time.sleep(0.1)  # Small delay to ensure interleaving
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Each thread should have its own value
        assert len(results) == 5
        for i in range(5):
            assert results[i] == f"value_{i}"
