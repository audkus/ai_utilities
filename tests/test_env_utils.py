"""
Tests for env_utils module.

This module tests environment variable utilities to ensure proper isolation
and cleanup functionality.
"""

import os
import pytest
from unittest.mock import patch

from ai_utilities.env_utils import (
    cleanup_ai_env_vars,
    get_ai_env_vars,
    validate_ai_env_vars,
    isolated_env_context
)


class TestCleanupAiEnvVars:
    """Test cleanup_ai_env_vars function."""
    
    def test_cleanup_ai_env_vars_removes_ai_variables(self):
        """Test that cleanup removes all AI_ variables."""
        # Set up some AI environment variables
        os.environ['AI_API_KEY'] = 'test-key'
        os.environ['AI_MODEL'] = 'test-model'
        os.environ['OTHER_VAR'] = 'should-remain'
        
        try:
            cleanup_ai_env_vars()
            
            # AI variables should be removed
            assert 'AI_API_KEY' not in os.environ
            assert 'AI_MODEL' not in os.environ
            
            # Non-AI variables should remain
            assert os.environ['OTHER_VAR'] == 'should-remain'
        finally:
            # Clean up any remaining variables
            for var in ['AI_API_KEY', 'AI_MODEL']:
                if var in os.environ:
                    del os.environ[var]
    
    def test_cleanup_ai_env_vars_with_no_ai_variables(self):
        """Test cleanup when no AI variables exist."""
        # Ensure no AI variables exist
        ai_vars = [k for k in os.environ.keys() if k.startswith('AI_')]
        for var in ai_vars:
            del os.environ[var]
        
        # Should not raise an error
        cleanup_ai_env_vars()
    
    def test_cleanup_ai_env_vars_with_empty_values(self):
        """Test cleanup with empty AI variable values."""
        os.environ['AI_EMPTY'] = ''
        os.environ['AI_API_KEY'] = 'key'
        
        try:
            cleanup_ai_env_vars()
            
            # Both should be removed regardless of value
            assert 'AI_EMPTY' not in os.environ
            assert 'AI_API_KEY' not in os.environ
        finally:
            for var in ['AI_EMPTY', 'AI_API_KEY']:
                if var in os.environ:
                    del os.environ[var]


class TestGetAiEnvVars:
    """Test get_ai_env_vars function."""
    
    def test_get_ai_env_vars_returns_only_ai_variables(self):
        """Test that only AI_ variables are returned."""
        # Set up test environment
        os.environ['AI_API_KEY'] = 'test-key'
        os.environ['AI_MODEL'] = 'test-model'
        os.environ['OTHER_VAR'] = 'should-not-appear'
        
        try:
            result = get_ai_env_vars()
            
            # Should only contain AI variables
            assert 'AI_API_KEY' in result
            assert 'AI_MODEL' in result
            assert 'OTHER_VAR' not in result
            assert result['AI_API_KEY'] == 'test-key'
            assert result['AI_MODEL'] == 'test-model'
        finally:
            # Clean up
            for var in ['AI_API_KEY', 'AI_MODEL']:
                if var in os.environ:
                    del os.environ[var]
    
    def test_get_ai_env_vars_with_no_ai_variables(self):
        """Test when no AI variables exist."""
        # Ensure no AI variables
        ai_vars = [k for k in os.environ.keys() if k.startswith('AI_')]
        for var in ai_vars:
            del os.environ[var]
        
        result = get_ai_env_vars()
        assert result == {}
    
    def test_get_ai_env_vars_with_case_sensitivity(self):
        """Test that function is case sensitive."""
        os.environ['AI_API_KEY'] = 'test-key'
        os.environ['ai_api_key'] = 'lowercase-key'  # Should not be included
        os.environ['Ai_Api_Key'] = 'mixed-key'     # Should not be included
        
        try:
            result = get_ai_env_vars()
            
            # Only uppercase AI_ should be included
            assert 'AI_API_KEY' in result
            assert 'ai_api_key' not in result
            assert 'Ai_Api_Key' not in result
        finally:
            for var in ['AI_API_KEY', 'ai_api_key', 'Ai_Api_Key']:
                if var in os.environ:
                    del os.environ[var]


class TestValidateAiEnvVars:
    """Test validate_ai_env_vars function."""
    
    def test_validate_ai_env_vars_filters_known_variables(self):
        """Test that only known AI variables are returned."""
        # Set up test environment with known and unknown variables
        os.environ['AI_API_KEY'] = 'test-key'
        os.environ['AI_MODEL'] = 'test-model'
        os.environ['AI_UNKNOWN_VAR'] = 'unknown'
        os.environ['OTHER_VAR'] = 'not-ai'
        
        try:
            result = validate_ai_env_vars()
            
            # Should only include known AI variables
            assert 'AI_API_KEY' in result
            assert 'AI_MODEL' in result
            assert 'AI_UNKNOWN_VAR' not in result
            assert 'OTHER_VAR' not in result
        finally:
            # Clean up
            for var in ['AI_API_KEY', 'AI_MODEL', 'AI_UNKNOWN_VAR']:
                if var in os.environ:
                    del os.environ[var]
    
    def test_validate_ai_env_vars_with_all_known_variables(self):
        """Test with all known AI variables."""
        known_vars = {
            'AI_API_KEY', 'AI_MODEL', 'AI_TEMPERATURE', 'AI_MAX_TOKENS',
            'AI_BASE_URL', 'AI_TIMEOUT', 'AI_UPDATE_CHECK_DAYS', 'AI_USE_AI',
            'AI_MEMORY_THRESHOLD', 'AI_MODEL_RPM', 'AI_MODEL_TPM', 'AI_MODEL_TPD',
            'AI_GPT_4_RPM', 'AI_GPT_4_TPM', 'AI_GPT_4_TPD',
            'AI_GPT_3_5_TURBO_RPM', 'AI_GPT_3_5_TURBO_TPM', 'AI_GPT_3_5_TURBO_TPD',
            'AI_GPT_4_TURBO_RPM', 'AI_GPT_4_TURBO_TPM', 'AI_GPT_4_TURBO_TPD',
            'AI_USAGE_SCOPE', 'AI_USAGE_CLIENT_ID'
        }
        
        # Set all known variables
        for var in known_vars:
            os.environ[var] = f'value-{var.lower()}'
        
        try:
            result = validate_ai_env_vars()
            
            # All known variables should be included
            assert set(result.keys()) == known_vars
            
            # Values should be preserved
            for var in known_vars:
                assert result[var] == f'value-{var.lower()}'
        finally:
            # Clean up
            for var in known_vars:
                if var in os.environ:
                    del os.environ[var]
    
    def test_validate_ai_env_vars_with_no_known_variables(self):
        """Test when no known AI variables exist."""
        # Clear all known AI environment variables first
        ai_vars_to_clear = ['AI_API_KEY', 'AI_BASE_URL', 'AI_MODEL', 'AI_TEMPERATURE', 'AI_MAX_TOKENS', 'AI_TIMEOUT']
        cleared_vars = {}
        
        for var in ai_vars_to_clear:
            if var in os.environ:
                cleared_vars[var] = os.environ[var]
                del os.environ[var]
        
        try:
            os.environ['AI_UNKNOWN'] = 'unknown'
            result = validate_ai_env_vars()
            assert result == {}
        finally:
            if 'AI_UNKNOWN' in os.environ:
                del os.environ['AI_UNKNOWN']
            # Restore cleared variables
            for var, value in cleared_vars.items():
                os.environ[var] = value


class TestIsolatedEnvContext:
    """Test isolated_env_context context manager."""
    
    def test_isolated_env_context_sets_and_restores_variables(self):
        """Test that variables are set and properly restored."""
        # Check for pre-existing AI variables
        pre_existing_vars = {}
        ai_vars = ['AI_API_KEY', 'AI_BASE_URL', 'AI_MODEL', 'AI_TEMPERATURE', 'AI_MAX_TOKENS', 'AI_TIMEOUT']
        for var in ai_vars:
            if var in os.environ:
                pre_existing_vars[var] = os.environ[var]
        
        # Set initial state
        os.environ['EXISTING_VAR'] = 'original-value'
        
        env_vars = {
            'AI_API_KEY': 'test-key',
            'EXISTING_VAR': 'modified-value',
            'NEW_VAR': 'new-value'
        }
        
        try:
            with isolated_env_context(env_vars):
                # Variables should be set within context
                assert os.environ['AI_API_KEY'] == 'test-key'
                assert os.environ['EXISTING_VAR'] == 'modified-value'
                assert os.environ['NEW_VAR'] == 'new-value'
            
            # Variables should be restored after context
            assert os.environ['EXISTING_VAR'] == 'original-value'
            
            # AI_API_KEY should be restored to its original state (or removed if it didn't exist)
            if 'AI_API_KEY' in pre_existing_vars:
                assert os.environ['AI_API_KEY'] == pre_existing_vars['AI_API_KEY']
            else:
                assert 'AI_API_KEY' not in os.environ
                
            assert 'NEW_VAR' not in os.environ
        finally:
            # Clean up any remaining variables
            for var in ['NEW_VAR']:
                if var in os.environ:
                    del os.environ[var]
            # Restore pre-existing variables
            for var, value in pre_existing_vars.items():
                os.environ[var] = value
    
    def test_isolated_env_context_with_no_variables(self):
        """Test context manager with no variables."""
        # Should not raise an error
        with isolated_env_context():
            pass
    
    def test_isolated_env_context_with_empty_dict(self):
        """Test context manager with empty dictionary."""
        with isolated_env_context({}):
            pass
    
    def test_isolated_env_context_restores_on_exception(self):
        """Test that environment is restored even if exception occurs."""
        # Check for pre-existing AI variables
        pre_existing_vars = {}
        ai_vars = ['AI_API_KEY', 'AI_BASE_URL', 'AI_MODEL', 'AI_TEMPERATURE', 'AI_MAX_TOKENS', 'AI_TIMEOUT']
        for var in ai_vars:
            if var in os.environ:
                pre_existing_vars[var] = os.environ[var]
        
        os.environ['EXISTING_VAR'] = 'original-value'
        
        env_vars = {'AI_API_KEY': 'test-key'}
        
        try:
            with pytest.raises(ValueError):
                with isolated_env_context(env_vars):
                    assert os.environ['AI_API_KEY'] == 'test-key'
                    raise ValueError("Test exception")
            
            # Environment should still be restored
            assert os.environ['EXISTING_VAR'] == 'original-value'
            
            # AI_API_KEY should be restored to its original state (or removed if it didn't exist)
            if 'AI_API_KEY' in pre_existing_vars:
                assert os.environ['AI_API_KEY'] == pre_existing_vars['AI_API_KEY']
            else:
                assert 'AI_API_KEY' not in os.environ
        finally:
            # Restore pre-existing variables
            for var, value in pre_existing_vars.items():
                os.environ[var] = value
    
    def test_isolated_env_context_nested(self):
        """Test nested context managers."""
        os.environ['EXISTING_VAR'] = 'original'
        
        try:
            with isolated_env_context({'OUTER': 'outer-value'}):
                assert os.environ['OUTER'] == 'outer-value'
                
                with isolated_env_context({'INNER': 'inner-value', 'OUTER': 'nested-value'}):
                    assert os.environ['INNER'] == 'inner-value'
                    assert os.environ['OUTER'] == 'nested-value'
                
                # Outer context should be restored
                assert os.environ['OUTER'] == 'outer-value'
                assert 'INNER' not in os.environ
            
            # Everything should be restored
            assert os.environ['EXISTING_VAR'] == 'original'
            assert 'OUTER' not in os.environ
            assert 'INNER' not in os.environ
        finally:
            for var in ['OUTER', 'INNER']:
                if var in os.environ:
                    del os.environ[var]


class TestIntegration:
    """Integration tests for env_utils functions."""
    
    def test_cleanup_and_get_interaction(self):
        """Test interaction between cleanup and get functions."""
        # Set up multiple AI variables
        ai_vars = {
            'AI_API_KEY': 'key1',
            'AI_MODEL': 'model1',
            'AI_TEMPERATURE': '0.5'
        }
        
        for key, value in ai_vars.items():
            os.environ[key] = value
        
        try:
            # Verify variables are there
            result = get_ai_env_vars()
            assert len(result) >= 3
            
            # Clean up
            cleanup_ai_env_vars()
            
            # Verify they're gone
            result = get_ai_env_vars()
            assert result == {}
        finally:
            # Ensure cleanup
            cleanup_ai_env_vars()
    
    def test_validate_and_isolated_context_interaction(self):
        """Test interaction between validation and isolated context."""
        # Check for pre-existing AI variables
        pre_existing_vars = {}
        ai_vars = ['AI_API_KEY', 'AI_BASE_URL', 'AI_MODEL', 'AI_TEMPERATURE', 'AI_MAX_TOKENS', 'AI_TIMEOUT']
        for var in ai_vars:
            if var in os.environ:
                pre_existing_vars[var] = os.environ[var]
        
        # Clear all AI variables for clean test start
        for var in ai_vars:
            if var in os.environ:
                del os.environ[var]
        
        os.environ['AI_API_KEY'] = 'original-key'
        os.environ['AI_UNKNOWN'] = 'unknown-value'
        
        try:
            # Initial validation should include known variables
            result = validate_ai_env_vars()
            assert 'AI_API_KEY' in result
            assert 'AI_UNKNOWN' not in result
            
            # Use isolated context to modify environment
            with isolated_env_context({'AI_MODEL': 'test-model', 'AI_UNKNOWN': 'temp'}):
                result = validate_ai_env_vars()
                assert 'AI_API_KEY' in result  # Still there from original
                assert 'AI_MODEL' in result   # Added by context
                assert 'AI_UNKNOWN' not in result  # Still filtered out
            
            # Back to original state
            result = validate_ai_env_vars()
            assert 'AI_API_KEY' in result
            assert 'AI_MODEL' not in result
        finally:
            cleanup_ai_env_vars()
            # Restore pre-existing variables
            for var, value in pre_existing_vars.items():
                os.environ[var] = value
