"""Tests for environment overrides using contextvars."""

import asyncio
import os
import sys

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_utilities.client import AiSettings
from ai_utilities.env_overrides import get_env_overrides, override_env


class TestEnvOverrides:
    """Test environment override functionality."""
    
    def test_get_env_overrides_default(self):
        """Test that get_env_overrides returns empty dict by default."""
        overrides = get_env_overrides()
        assert overrides == {}
        assert isinstance(overrides, dict)
    
    def test_override_env_basic(self):
        """Test basic override_env functionality."""
        # Set up initial environment
        os.environ['AI_MODEL'] = 'test-model-1'
        os.environ['AI_TEMPERATURE'] = '0.7'
        
        # Test with overrides
        with override_env({'AI_MODEL': 'test-model-2', 'AI_TEMPERATURE': '1.0'}):
            overrides = get_env_overrides()
            assert overrides['AI_MODEL'] == 'test-model-2'
            assert overrides['AI_TEMPERATURE'] == '1.0'
        
        # Verify overrides are cleared
        overrides = get_env_overrides()
        assert overrides == {}
        
        # Verify original environment is unchanged
        assert os.environ['AI_MODEL'] == 'test-model-1'
        assert os.environ['AI_TEMPERATURE'] == '0.7'
        
        # Clean up
        del os.environ['AI_MODEL']
        del os.environ['AI_TEMPERATURE']
    
    def test_override_env_nested(self):
        """Test nested override_env contexts."""
        with override_env({'AI_MODEL': 'test-model-2'}):
            # First level
            overrides = get_env_overrides()
            assert overrides['AI_MODEL'] == 'test-model-2'
            
            with override_env({'AI_TEMPERATURE': '0.9'}):
                # Second level - should merge with first
                overrides = get_env_overrides()
                assert overrides['AI_MODEL'] == 'test-model-2'
                assert overrides['AI_TEMPERATURE'] == '0.9'
                
                with override_env({'AI_MODEL': 'test-model-1'}):
                    # Third level - should override model
                    overrides = get_env_overrides()
                    assert overrides['AI_MODEL'] == 'test-model-1'
                    assert overrides['AI_TEMPERATURE'] == '0.9'
                
                # Back to second level
                overrides = get_env_overrides()
                assert overrides['AI_MODEL'] == 'test-model-2'
                assert overrides['AI_TEMPERATURE'] == '0.9'
            
            # Back to first level
            overrides = get_env_overrides()
            assert overrides['AI_MODEL'] == 'test-model-2'
            assert 'AI_TEMPERATURE' not in overrides
        
        # All cleared
        overrides = get_env_overrides()
        assert overrides == {}
    
    def test_override_env_type_conversion(self):
        """Test that values are converted to strings."""
        with override_env({
            'AI_MODEL': 'test-model-1',
            'AI_TEMPERATURE': 0.9,
            'AI_MAX_TOKENS': 2000,
            'AI_TIMEOUT': 30.5
        }):
            overrides = get_env_overrides()
            assert all(isinstance(v, str) for v in overrides.values())
            assert overrides['AI_TEMPERATURE'] == '0.9'
            assert overrides['AI_MAX_TOKENS'] == '2000'
            assert overrides['AI_TIMEOUT'] == '30.5'
    
    def test_override_env_exception_handling(self):
        """Test that environment is restored even if exception occurs."""
        os.environ['AI_MODEL'] = 'test-model-1'
        
        try:
            with override_env({'AI_MODEL': 'test-model-2'}):
                overrides = get_env_overrides()
                assert overrides['AI_MODEL'] == 'test-model-2'
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected
        
        # Environment should be restored
        overrides = get_env_overrides()
        assert overrides == {}
        assert os.environ['AI_MODEL'] == 'test-model-1'
        
        # Clean up
        del os.environ['AI_MODEL']
    
    def test_ai_settings_integration_behavior(self):
        """Test AiSettings.settings_customise_sources behavior with overrides."""
        # Test that AiSettings properly integrates with override_env
        # This validates the settings_customise_sources behavior without testing internals
        
        # Test with no overrides - should use defaults
        settings = AiSettings()
        assert settings.model == 'test-model-1'  # Default value
        assert settings.temperature == 0.7  # Default value
        
        # Test with overrides - should use override values
        with override_env({
            'AI_MODEL': 'test-model-2',
            'AI_TEMPERATURE': '0.9',
            'AI_MAX_TOKENS': '2000',
            'AI_TIMEOUT': '60'
        }):
            settings = AiSettings()
            assert settings.model == 'test-model-2'
            assert settings.temperature == 0.9
            assert settings.max_tokens == 2000
            assert settings.timeout == 60
    
    def test_override_only_baseline(self):
        """Test 'override only' baseline - no env vars, only overrides."""
        # Ensure no AI_MODEL in os.environ
        if 'AI_MODEL' in os.environ:
            del os.environ['AI_MODEL']
        
        # Test with only override_env, no os.environ
        with override_env({"AI_MODEL": "test-model-2"}):
            settings = AiSettings()
            assert settings.model == "test-model-2"
        
        # Clean up
        if 'AI_MODEL' in os.environ:
            del os.environ['AI_MODEL']
    
    @pytest.mark.asyncio
    async def test_task_inheritance_no_crosstalk(self):
        """Test task inheritance with asyncio.gather - ensure no cross-talk between tasks."""
        import asyncio
        
        async def task_with_override(model_name: str, temperature: float) -> tuple[str, float]:
            """Task that creates AiSettings with specific overrides."""
            with override_env({
                "AI_MODEL": model_name,
                "AI_TEMPERATURE": str(temperature)
            }):
                # Add a small delay to encourage task switching
                await asyncio.sleep(0.01)
                settings = AiSettings()
                return settings.model, settings.temperature
        
        # Run multiple tasks concurrently with different overrides
        tasks = [
            task_with_override("test-model-1", 0.7),
            task_with_override("test-model-2", 0.3),
            task_with_override("test-model-1-turbo", 0.9),
            task_with_override("test-model-1-32k", 0.1)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Each task should see its own values, no cross-talk
        expected = [
            ("test-model-1", 0.7),
            ("test-model-2", 0.3),
            ("test-model-1-turbo", 0.9),
            ("test-model-1-32k", 0.1)
        ]
        
        assert results == expected
        
        # Verify no context pollution after tasks complete
        overrides = get_env_overrides()
        assert overrides == {}
    
    def test_ai_settings_integration(self):
        """Test AiSettings integration with environment overrides."""
        # Set up initial environment
        os.environ['AI_MODEL'] = 'test-model-1'
        os.environ['AI_TEMPERATURE'] = '0.7'
        
        # Test default behavior (no overrides)
        settings = AiSettings()
        assert settings.model == 'test-model-1'
        assert settings.temperature == 0.7
        
        # Test with overrides
        with override_env({'AI_MODEL': 'test-model-2', 'AI_TEMPERATURE': '1.0'}):
            settings = AiSettings()
            assert settings.model == 'test-model-2'
            assert settings.temperature == 1.0
        
        # Test that original environment is restored
        settings = AiSettings()
        assert settings.model == 'test-model-1'
        assert settings.temperature == 0.7
        
        # Clean up
        del os.environ['AI_MODEL']
        del os.environ['AI_TEMPERATURE']
    
    def test_ai_settings_precedence(self):
        """Test that explicit kwargs have highest precedence."""
        os.environ['AI_MODEL'] = 'test-model-1'
        os.environ['AI_TEMPERATURE'] = '0.7'
        
        with override_env({'AI_MODEL': 'test-model-2', 'AI_TEMPERATURE': '1.0'}):
            # Explicit kwargs should override both environment and overrides
            settings = AiSettings(model='test-model-1-turbo', temperature=0.5)
            assert settings.model == 'test-model-1-turbo'
            assert settings.temperature == 0.5
            
            # Only temperature overridden explicitly
            settings = AiSettings(temperature=0.5)
            assert settings.model == 'test-model-2'  # From override
            assert settings.temperature == 0.5      # From kwargs
        
        # Clean up
        del os.environ['AI_MODEL']
        del os.environ['AI_TEMPERATURE']
    
    @pytest.mark.asyncio
    async def test_async_isolation(self):
        """Test that environment overrides work correctly in async contexts."""
        os.environ['AI_MODEL'] = 'test-model-1'
        
        async def task1():
            with override_env({'AI_MODEL': 'test-model-2'}):
                settings = AiSettings()
                await asyncio.sleep(0.1)  # Allow other tasks to run
                return settings.model
        
        async def task2():
            with override_env({'AI_MODEL': 'test-model-1-turbo'}):
                settings = AiSettings()
                await asyncio.sleep(0.05)  # Allow other tasks to run
                return settings.model
        
        # Run tasks concurrently
        results = await asyncio.gather(task1(), task2())
        
        # Each task should have its own isolated environment
        assert 'test-model-2' in results
        assert 'test-model-1-turbo' in results
        
        # Original environment should be unchanged
        settings = AiSettings()
        assert settings.model == 'test-model-1'
        
        # Clean up
        del os.environ['AI_MODEL']
    
    def test_thread_isolation(self):
        """Test that environment overrides work correctly across threads."""
        import threading
        import time
        
        os.environ['AI_MODEL'] = 'test-model-1'
        results = {}
        
        def thread_task(thread_id, model_name):
            with override_env({'AI_MODEL': model_name}):
                time.sleep(0.1)  # Allow other threads to run
                settings = AiSettings()
                results[thread_id] = settings.model
        
        # Create multiple threads with different overrides
        threads = [
            threading.Thread(target=thread_task, args=(1, 'test-model-2')),
            threading.Thread(target=thread_task, args=(2, 'test-model-1-turbo')),
            threading.Thread(target=thread_task, args=(3, 'test-model-1-32k')),
        ]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Each thread should have its own isolated environment
        assert len(results) == 3
        assert 'test-model-2' in results.values()
        assert 'test-model-1-turbo' in results.values()
        assert 'test-model-1-32k' in results.values()
        
        # Original environment should be unchanged
        settings = AiSettings()
        assert settings.model == 'test-model-1'
        
        # Clean up
        del os.environ['AI_MODEL']
    
    def test_no_os_environ_mutation(self):
        """Test that override_env does not mutate os.environ."""
        original_env = dict(os.environ)
        
        with override_env({
            'AI_MODEL': 'test-model-2',
            'AI_TEMPERATURE': '0.9',
            'AI_CUSTOM_VAR': 'test'
        }):
            # os.environ should be unchanged
            assert os.environ.get('AI_MODEL') == original_env.get('AI_MODEL')
            assert os.environ.get('AI_TEMPERATURE') == original_env.get('AI_TEMPERATURE')
            assert 'AI_CUSTOM_VAR' not in os.environ
        
        # Environment should be exactly as it was
        assert os.environ == original_env
