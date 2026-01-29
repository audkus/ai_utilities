"""Comprehensive tests for AiSettings source priority and environment mapping."""

import asyncio
import os
import sys
import threading

import pytest
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_utilities import AiSettings
from ai_utilities.env_overrides import override_env


class TestAiSettingsPrecedence:
    """Test AiSettings source priority: init kwargs > override_env > os.environ > defaults."""
    
    def test_defaults_fallback(self):
        """Test 1: Defaults fallback (no env, no override)."""
        # Ensure no environment variables are set
        env_vars = [k for k in os.environ.keys() if k.startswith('AI_')]
        for var in env_vars:
            del os.environ[var]
        
        settings = AiSettings()
        
        # Verify defaults
        assert settings.model is None
        assert settings.temperature == 0.7
        assert settings.max_tokens is None
        assert settings.timeout == 30  # Default timeout
    
    def test_os_environ_overrides_defaults(self):
        """Test 2: os.environ overrides defaults."""
        from ai_utilities.env_overrides import override_env
        
        # Test with environment variables
        with override_env({
            "AI_MODEL": "env-model",
            "AI_TEMPERATURE": "1.2"
        }):
            settings = AiSettings()
            assert settings.model == "env-model"
            assert settings.temperature == 1.2
    
    def test_override_env_overrides_os_environ(self):
        """Test 3: override_env overrides os.environ."""
        # Set base environment
        os.environ["AI_MODEL"] = "env-model"
        original_env = dict(os.environ)
        
        try:
            # Test override_env takes precedence
            with override_env({"AI_MODEL": "override-model"}):
                settings = AiSettings()
                assert settings.model == "override-model"
            
            # After context, should revert to env value
            settings = AiSettings()
            assert settings.model == "env-model"
            
            # Verify os.environ was never mutated
            assert os.environ["AI_MODEL"] == "env-model"
            assert dict(os.environ) == original_env
            
        finally:
            # Cleanup
            del os.environ["AI_MODEL"]
    
    def test_init_kwargs_override_all(self):
        """Test 4: init kwargs override override_env + os.environ (top priority)."""
        # Set environment and override
        os.environ["AI_MODEL"] = "env-model"
        original_env = dict(os.environ)
        
        try:
            with override_env({"AI_MODEL": "override-model"}):
                settings = AiSettings(model="kw-model")
                assert settings.model == "kw-model"  # kwargs win
            
            # Verify environment unchanged
            assert os.environ["AI_MODEL"] == "env-model"
            assert dict(os.environ) == original_env
            
        finally:
            del os.environ["AI_MODEL"]
    
    def test_nested_override_env_merges_and_restores(self):
        """Test 5: Nested override_env merges correctly and restores."""
        # Clean environment
        env_vars = [k for k in os.environ.keys() if k.startswith('AI_')]
        for var in env_vars:
            del os.environ[var]
        
        try:
            with override_env({"AI_MODEL": "outer-model"}):
                # Inner context should merge with outer
                with override_env({"AI_TEMPERATURE": "1.0"}):
                    settings = AiSettings()
                    assert settings.model == "outer-model"  # from outer
                    assert settings.temperature == 1.0      # from inner
                
                # After inner exits, outer still applies
                settings = AiSettings()
                assert settings.model == "outer-model"
                assert settings.temperature == 0.7  # back to default
            
            # After outer exits, everything back to default
            settings = AiSettings(_env_file=None)
            assert settings.model is None
            assert settings.temperature == 0.7    # default
            
        finally:
            # Cleanup any remaining env vars
            env_vars = [k for k in os.environ.keys() if k.startswith('AI_')]
            for var in env_vars:
                del os.environ[var]
    
    def test_mapping_max_tokens(self):
        """Test 6: Mapping test: AI_MAX_TOKENS -> max_tokens (int)."""
        # Test with override_env
        with override_env({"AI_MAX_TOKENS": "123"}):
            settings = AiSettings()
            assert settings.max_tokens == 123
        
        # Test with os.environ
        env_vars = [k for k in os.environ.keys() if k.startswith('AI_')]
        for var in env_vars:
            del os.environ[var]
        
        try:
            os.environ["AI_MAX_TOKENS"] = "456"
            settings = AiSettings()
            assert settings.max_tokens == 456
        finally:
            if "AI_MAX_TOKENS" in os.environ:
                del os.environ["AI_MAX_TOKENS"]
    
    def test_mapping_update_check_days(self):
        """Test 7: Mapping test: AI_UPDATE_CHECK_DAYS -> update_check_days (int)."""
        with override_env({"AI_UPDATE_CHECK_DAYS": "10"}):
            settings = AiSettings()
            assert settings.update_check_days == 10
    
    def test_non_specified_override_key_ignored(self):
        """Test 8: Non-specified override key is ignored (extra='ignore')."""
        # Clean environment
        env_vars = [k for k in os.environ.keys() if k.startswith('AI_')]
        for var in env_vars:
            del os.environ[var]
        
        try:
            with override_env({"AI_DOES_NOT_EXIST": "x"}):
                settings = AiSettings()
                # Should use defaults, no exception raised
                assert settings.model is None
                assert settings.temperature == 0.7
        finally:
            # Cleanup
            env_vars = [k for k in os.environ.keys() if k.startswith('AI_')]
            for var in env_vars:
                del os.environ[var]
    
    def test_type_conversion_override_env(self):
        """Test 9: Type conversion behavior for override_env values."""
        with override_env({"AI_TEMPERATURE": "0.9"}):
            settings = AiSettings()
            assert settings.temperature == 0.9
            assert isinstance(settings.temperature, float)
        
        with override_env({"AI_TIMEOUT": "60"}):
            settings = AiSettings()
            assert settings.timeout == 60
            assert isinstance(settings.timeout, int)
    
    def test_error_behavior_invalid_override_values(self):
        """Test 10: Error behavior for invalid override values."""
        # Test invalid temperature
        with override_env({"AI_TEMPERATURE": "not-a-float"}):
            with pytest.raises(ValueError):  # Pydantic raises ValidationError which inherits from ValueError
                AiSettings()
        
        # Test invalid timeout
        with override_env({"AI_TIMEOUT": "not-an-int"}):
            with pytest.raises(ValueError):
                AiSettings()
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_async_safety_ai_settings_boundary(self):
        """Test 11: Thread + async safety at AiSettings boundary - async version."""
        async def task_with_override(model_name: str) -> str:
            """Task that creates AiSettings with specific override."""
            with override_env({"AI_MODEL": model_name}):
                await asyncio.sleep(0)  # Allow task switching
                settings = AiSettings()
                return settings.model
        
        # Run concurrent tasks with different overrides
        tasks = [
            task_with_override("async-model-1"),
            task_with_override("async-model-2"),
            task_with_override("async-model-3"),
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Each task should see its own value
        expected = ["async-model-1", "async-model-2", "async-model-3"]
        assert results == expected
    
    @pytest.mark.slow
    def test_thread_safety_ai_settings_boundary(self):
        """Test 11: Thread + async safety at AiSettings boundary - thread version."""
        def thread_with_override(model_name: str, results: list, index: int):
            """Thread function that creates AiSettings with specific override."""
            with override_env({"AI_MODEL": model_name}):
                settings = AiSettings()
                results[index] = settings.model
        
        # Run concurrent threads with different overrides
        results = [None] * 3
        threads = [
            threading.Thread(target=thread_with_override, args=("thread-model-1", results, 0)),
            threading.Thread(target=thread_with_override, args=("thread-model-2", results, 1)),
            threading.Thread(target=thread_with_override, args=("thread-model-3", results, 2)),
        ]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Each thread should see its own value
        expected = ["thread-model-1", "thread-model-2", "thread-model-3"]
        assert results == expected
    
    def test_create_isolated_deprecation_behavior(self):
        """Test 12: create_isolated delegates to override_env (if kept)."""
        # Set environment
        os.environ["AI_MODEL"] = "env-model"
        original_env = dict(os.environ)
        
        try:
            # Test create_isolated behavior
            settings = AiSettings.create_isolated({"AI_MODEL": "iso-model"})
            assert settings.model == "iso-model"
            
            # Verify os.environ was not mutated
            assert os.environ["AI_MODEL"] == "env-model"
            assert dict(os.environ) == original_env
            
        finally:
            del os.environ["AI_MODEL"]
    
    def test_explicit_precedence_chain(self):
        """Test explicit precedence chain: init kwargs > override_env > os.environ > defaults."""
        # Set up all levels
        os.environ["AI_MODEL"] = "env-model"
        original_env = dict(os.environ)
        
        try:
            with override_env({"AI_MODEL": "override-model"}):
                # Init kwargs should win over everything
                settings = AiSettings(model="kw-model")
                assert settings.model == "kw-model"  # 1st priority
            
            # After context, override_env should win over env
            with override_env({"AI_MODEL": "override-model"}):
                settings = AiSettings()
                assert settings.model == "override-model"  # 2nd priority
            
            # Without override_env, os.environ should win over defaults
            settings = AiSettings()
            assert settings.model == "env-model"  # 3rd priority
            
            # Clean environment should use defaults
            del os.environ["AI_MODEL"]
            settings = AiSettings(_env_file=None)
            assert settings.model is None  # 4th priority (defaults)
            
        finally:
            # Restore environment
            if "AI_MODEL" in original_env:
                os.environ["AI_MODEL"] = original_env["AI_MODEL"]
    
    def test_comprehensive_mapping_coverage(self):
        """Test mapping coverage for key AI_* environment variables."""
        test_mappings = {
            "AI_MODEL": ("test-model", lambda s: s.model),
            "AI_TEMPERATURE": ("0.5", lambda s: s.temperature),
            "AI_MAX_TOKENS": ("2048", lambda s: s.max_tokens),
            "AI_TIMEOUT": ("120", lambda s: s.timeout),
            "AI_UPDATE_CHECK_DAYS": ("15", lambda s: s.update_check_days),
        }
        
        for env_key, (env_value, accessor) in test_mappings.items():
            with override_env({env_key: env_value}):
                settings = AiSettings()
                actual_value = accessor(settings)
                if env_key == "AI_TEMPERATURE":
                    assert actual_value == float(env_value)
                elif env_key in ["AI_MAX_TOKENS", "AI_TIMEOUT", "AI_UPDATE_CHECK_DAYS"]:
                    assert actual_value == int(env_value)
                else:
                    assert actual_value == env_value


class TestEnvironmentIsolation:
    """Test that override_env doesn't mutate os.environ."""
    
    def test_os_environ_unchanged_during_override_env(self):
        """Test os.environ unchanged assertion during override_env."""
        original_env = dict(os.environ)
        
        # Add some test environment variables
        test_vars = {
            "AI_MODEL": "test-model",
            "AI_TEMPERATURE": "0.8",
            "AI_MAX_TOKENS": "1024"
        }
        
        with override_env(test_vars):
            # os.environ should be unchanged
            assert dict(os.environ) == original_env
            
            # But AiSettings should see the overrides
            settings = AiSettings()
            assert settings.model == "test-model"
            assert settings.temperature == 0.8
            assert settings.max_tokens == 1024
        
        # Environment should be exactly as it was
        assert dict(os.environ) == original_env

    def test_defaults_when_nothing_set(self):
        """Test defaults when nothing set."""
        with patch.dict(os.environ, {}, clear=True):
            settings = AiSettings(_env_file=None)
            assert settings.api_key is None
            assert settings.model is None
