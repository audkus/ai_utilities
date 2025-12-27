"""Tests for environment variable utilities to prevent contamination."""

import os
import sys

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_utilities.client import AiSettings
from ai_utilities.config_models import AIConfig
from ai_utilities.env_overrides import (
    get_ai_env,
    get_ai_env_bool,
    get_ai_env_float,
    get_ai_env_int,
    get_env_overrides,
    override_env,
)


class TestEnvironmentIsolation:
    """Test environment variable isolation utilities."""
    
    def test_isolated_env_context_basic(self):
        """Test basic isolated environment context."""
        # Set up initial environment
        os.environ['AI_MODEL'] = 'test-model-1'
        os.environ['AI_TEMPERATURE'] = '0.7'
        
        # Test isolated context
        with override_env({'AI_MODEL': 'test-model-2', 'AI_TEMPERATURE': '1.0'}):
            current_overrides = get_env_overrides()
            assert current_overrides['AI_MODEL'] == 'test-model-2'
            assert current_overrides['AI_TEMPERATURE'] == '1.0'
            
            # Test helper functions
            assert get_ai_env('MODEL') == 'test-model-2'
            assert get_ai_env_float('TEMPERATURE') == 1.0
        
        # Verify environment is restored
        current_overrides = get_env_overrides()
        assert current_overrides == {}
        
        # Verify original environment is intact
        assert os.environ['AI_MODEL'] == 'test-model-1'
        assert os.environ['AI_TEMPERATURE'] == '0.7'
        
        # Clean up
        del os.environ['AI_MODEL']
        del os.environ['AI_TEMPERATURE']
    
    def test_isolated_env_context_cleanup(self):
        """Test that isolated context cleans up properly."""
        # Set up initial environment
        os.environ['AI_MODEL'] = 'test-model-1'
        os.environ['AI_API_KEY'] = 'test-key'
        
        try:
            # Test isolated context with exception
            with override_env({'AI_MODEL': 'test-model-2'}):
                assert get_ai_env('MODEL') == 'test-model-2'
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected
        
        # Verify environment is restored even after exception
        current_overrides = get_env_overrides()
        assert current_overrides == {}
        assert os.environ['AI_MODEL'] == 'test-model-1'
        assert os.environ['AI_API_KEY'] == 'test-key'
        
        # Clean up
        del os.environ['AI_MODEL']
        del os.environ['AI_API_KEY']
    
    def test_ai_settings_isolation(self):
        """Test AiSettings with environment variable isolation."""
        # Set up initial environment
        os.environ['AI_MODEL'] = 'test-model-1'
        os.environ['AI_TEMPERATURE'] = '0.7'
        
        # Test isolated creation using new approach
        with override_env({
            'AI_MODEL': 'test-model-2',
            'AI_TEMPERATURE': '1.0'
        }):
            settings = AiSettings()
            assert settings.model == 'test-model-2'
            assert settings.temperature == 1.0
        
        # Verify original environment is intact
        assert os.environ['AI_MODEL'] == 'test-model-1'
        assert os.environ['AI_TEMPERATURE'] == '0.7'
        
        # Clean up
        del os.environ['AI_MODEL']
        del os.environ['AI_TEMPERATURE']
    
    def test_ai_settings_deprecated_isolated(self):
        """Test deprecated AiSettings.create_isolated still works."""
        # Set up initial environment
        os.environ['AI_MODEL'] = 'test-model-1'
        os.environ['AI_TEMPERATURE'] = '0.7'
        
        # Test deprecated method still works
        settings = AiSettings.create_isolated({
            'AI_MODEL': 'test-model-2',
            'AI_TEMPERATURE': '1.0'
        })
        
        assert settings.model == 'test-model-2'
        assert settings.temperature == 1.0
        
        # Verify original environment is intact
        assert os.environ['AI_MODEL'] == 'test-model-1'
        assert os.environ['AI_TEMPERATURE'] == '0.7'
        
        # Clean up
        del os.environ['AI_MODEL']
        del os.environ['AI_TEMPERATURE']
    
    def test_ai_config_isolation(self):
        """Test AIConfig with environment variable isolation."""
        # Set up initial environment
        os.environ['AI_MODEL_RPM'] = '1000'
        os.environ['AI_TEST_MODEL_1_RPM'] = '2000'
        
        # Test isolated creation
        with override_env({
            'AI_MODEL_RPM': '3000',
            'AI_TEST_MODEL_1_RPM': '4000'
        }):
            config = AIConfig()
            assert config.models['test-model-2'].requests_per_minute == 3000
            assert config.models['test-model-1'].requests_per_minute == 4000
        
        # Verify original environment is intact
        assert os.environ['AI_MODEL_RPM'] == '1000'
        assert os.environ['AI_TEST_MODEL_1_RPM'] == '2000'
        
        # Clean up
        del os.environ['AI_MODEL_RPM']
        del os.environ['AI_TEST_MODEL_1_RPM']
    
    def test_multiple_isolated_contexts(self):
        """Test multiple isolated contexts don't interfere with each other."""
        # First context
        with override_env({'AI_MODEL': 'test-model-2'}):
            settings1 = AiSettings()
            assert settings1.model == 'test-model-2'
            
            # Nested context
            with override_env({'AI_MODEL': 'test-model-1'}):
                settings2 = AiSettings()
                assert settings2.model == 'test-model-1'
            
            # Back to first context
            settings3 = AiSettings()
            assert settings3.model == 'test-model-2'
        
        # Environment should be clean
        current_overrides = get_env_overrides()
        assert current_overrides == {}
    
    def test_helper_functions(self):
        """Test environment helper functions."""
        with override_env({
            'AI_MODEL': 'test-model-1',
            'AI_TEMPERATURE': '0.9',
            'AI_MAX_TOKENS': '2000',
            'AI_USE_AI': 'true'
        }):
            assert get_ai_env('MODEL') == 'test-model-1'
            assert get_ai_env_float('TEMPERATURE') == 0.9
            assert get_ai_env_int('MAX_TOKENS') == 2000
            assert get_ai_env_bool('USE_AI') is True
            assert get_ai_env_bool('NONEXISTENT') is False
            assert get_ai_env('NONEXISTENT') is None
    
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


if __name__ == '__main__':
    pytest.main([__file__])
