"""Comprehensive tests for token_counter.py module - Phase 7B.

This module provides thorough testing for the TokenCounter class,
covering all counting methods, message token estimation, and model-specific adjustments.
"""

import pytest
from ai_utilities.token_counter import TokenCounter


class TestTokenCounter:
    """Test the TokenCounter class."""
    
    def test_class_constants(self):
        """Test that class constants are properly defined."""
        assert TokenCounter.WORD_TO_TOKEN_RATIO == 0.75
        assert TokenCounter.CHAR_TO_TOKEN_RATIO == 4.0
        assert TokenCounter.MESSAGE_OVERHEAD == 4
        assert TokenCounter.ROLE_OVERHEAD == 2
    
    def test_count_tokens_empty_text(self):
        """Test counting tokens for empty text."""
        assert TokenCounter.count_tokens("") == 0
        assert TokenCounter.count_tokens(None) == 0  # None should be treated as falsy
    
    def test_count_tokens_word_method(self):
        """Test counting tokens using word method."""
        text = "Hello world this is a test"
        # 6 words / 0.75 = 8 tokens
        expected = int(6 / 0.75)
        assert TokenCounter.count_tokens(text, "word") == expected
    
    def test_count_tokens_char_method(self):
        """Test counting tokens using character method."""
        text = "Hello world"
        # 11 chars / 4.0 = 2.75 -> 2 tokens (int conversion)
        expected = int(len(text) / 4.0)
        assert TokenCounter.count_tokens(text, "char") == expected
    
    def test_count_tokens_combined_method(self):
        """Test counting tokens using combined method."""
        text = "Hello world test"
        word_count = int(len(text.split()) / 0.75)
        char_count = int(len(text) / 4.0)
        expected = int((word_count + char_count) / 2)
        assert TokenCounter.count_tokens(text, "combined") == expected
    
    def test_count_tokens_invalid_method(self):
        """Test that invalid counting method raises ValueError."""
        with pytest.raises(ValueError, match="Unknown counting method: invalid"):
            TokenCounter.count_tokens("test text", "invalid")
    
    def test_count_tokens_default_method(self):
        """Test that default method is word-based."""
        text = "Hello world test"
        word_result = TokenCounter.count_tokens(text, "word")
        default_result = TokenCounter.count_tokens(text)
        assert word_result == default_result
    
    def test_count_message_tokens_empty_list(self):
        """Test counting tokens for empty message list."""
        assert TokenCounter.count_message_tokens([]) == 0
    
    def test_count_message_tokens_single_message(self):
        """Test counting tokens for a single message."""
        messages = [{"role": "user", "content": "Hello world"}]
        
        # Calculate expected: content tokens + role tokens + overhead
        content_tokens = TokenCounter.count_tokens("Hello world", "word")
        role_tokens = TokenCounter.count_tokens("user", "word")
        expected = content_tokens + role_tokens + TokenCounter.MESSAGE_OVERHEAD
        
        result = TokenCounter.count_message_tokens(messages, "word")
        assert result == expected
    
    def test_count_message_tokens_multiple_messages(self):
        """Test counting tokens for multiple messages."""
        messages = [
            {"role": "user", "content": "Hello world"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        result = TokenCounter.count_message_tokens(messages, "word")
        
        # Calculate expected manually
        expected = 0
        for msg in messages:
            content_tokens = TokenCounter.count_tokens(msg["content"], "word")
            role_tokens = TokenCounter.count_tokens(msg["role"], "word")
            expected += content_tokens + role_tokens + TokenCounter.MESSAGE_OVERHEAD
        
        assert result == expected
    
    def test_count_message_tokens_missing_fields(self):
        """Test counting tokens with missing message fields."""
        messages = [
            {"content": "Hello world"},  # Missing role
            {"role": "user"},  # Missing content
            {}  # Missing both
        ]
        
        result = TokenCounter.count_message_tokens(messages, "word")
        
        # Should handle missing fields gracefully
        expected = 0
        for msg in messages:
            content = msg.get("content", "")
            role = msg.get("role", "")
            content_tokens = TokenCounter.count_tokens(content, "word")
            role_tokens = TokenCounter.count_tokens(role, "word")
            expected += content_tokens + role_tokens + TokenCounter.MESSAGE_OVERHEAD
        
        assert result == expected
    
    def test_count_by_words(self):
        """Test the private _count_by_words method."""
        text = "Hello world test"
        expected = int(len(text.split()) / 0.75)
        assert TokenCounter._count_by_words(text) == expected
    
    def test_count_by_chars(self):
        """Test the private _count_by_chars method."""
        text = "Hello world test"
        expected = int(len(text) / 4.0)
        assert TokenCounter._count_by_chars(text) == expected
    
    def test_count_combined(self):
        """Test the private _count_combined method."""
        text = "Hello world test"
        word_count = TokenCounter._count_by_words(text)
        char_count = TokenCounter._count_by_chars(text)
        expected = int((word_count + char_count) / 2)
        assert TokenCounter._count_combined(text) == expected
    
    def test_estimate_response_tokens_default(self):
        """Test response token estimation with default factor."""
        prompt_tokens = 100
        expected = int(100 * 1.5)  # Default factor
        assert TokenCounter.estimate_response_tokens(prompt_tokens) == expected
    
    def test_estimate_response_tokens_custom_factor(self):
        """Test response token estimation with custom factor."""
        prompt_tokens = 100
        factor = 2.0
        expected = int(100 * factor)
        assert TokenCounter.estimate_response_tokens(prompt_tokens, factor) == expected
    
    def test_estimate_response_tokens_zero_prompt(self):
        """Test response token estimation with zero prompt tokens."""
        assert TokenCounter.estimate_response_tokens(0) == 0
    
    def test_count_tokens_for_model_default(self):
        """Test model-specific token counting with default model."""
        text = "Hello world test"
        base_count = TokenCounter.count_tokens(text, "combined")
        
        # Default model should use no adjustment (factor 1.0)
        result = TokenCounter.count_tokens_for_model(text, "unknown-model")
        assert result == base_count
    
    def test_count_tokens_for_model_known_models(self):
        """Test model-specific token counting for known models."""
        text = "Hello world test"
        base_count = TokenCounter.count_tokens(text, "combined")
        
        # Test each known model
        model_factors = {
            "test-model-1": 1.0,
            "test-model-3": 0.9,
            "test-model-2": 1.1,
            "test-model-6": 1.1,
        }
        
        for model, factor in model_factors.items():
            expected = int(base_count * factor)
            result = TokenCounter.count_tokens_for_model(text, model)
            assert result == expected
    
    def test_count_tokens_for_model_gpt35(self):
        """Test model-specific token counting for gpt-3.5-turbo."""
        text = "Hello world test"
        base_count = TokenCounter.count_tokens(text, "combined")
        
        # gpt-3.5-turbo should use default adjustment (1.0)
        result = TokenCounter.count_tokens_for_model(text, "gpt-3.5-turbo")
        assert result == base_count
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Very short text
        assert TokenCounter.count_tokens("a") >= 0
        
        # Text with only spaces
        assert TokenCounter.count_tokens("   ") >= 0
        
        # Text with special characters
        special_text = "Hello\n\tworld!@#"
        assert TokenCounter.count_tokens(special_text) >= 0
        
        # Very long text
        long_text = "word " * 1000
        assert TokenCounter.count_tokens(long_text) > 0
    
    def test_consistency_across_methods(self):
        """Test that methods produce consistent results."""
        text = "Hello world test"
        
        # All methods should produce positive integers
        word_count = TokenCounter.count_tokens(text, "word")
        char_count = TokenCounter.count_tokens(text, "char")
        combined_count = TokenCounter.count_tokens(text, "combined")
        
        assert isinstance(word_count, int)
        assert isinstance(char_count, int)
        assert isinstance(combined_count, int)
        
        assert word_count >= 0
        assert char_count >= 0
        assert combined_count >= 0
    
    def test_message_token_calculation_breakdown(self):
        """Test detailed message token calculation."""
        messages = [
            {"role": "user", "content": "Hello world"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        # Test with word method for predictable results
        result = TokenCounter.count_message_tokens(messages, "word")
        
        # Verify calculation includes overhead for each message
        base_tokens = 0
        for msg in messages:
            base_tokens += TokenCounter.count_tokens(msg["content"], "word")
            base_tokens += TokenCounter.count_tokens(msg["role"], "word")
        
        overhead = len(messages) * TokenCounter.MESSAGE_OVERHEAD
        expected = base_tokens + overhead
        
        assert result == expected
    
    def test_model_adjustment_factors(self):
        """Test that model adjustment factors are applied correctly."""
        text = "test message with multiple words"
        base_count = TokenCounter.count_tokens(text, "combined")
        
        # Test that adjustments are proportional
        efficient_model = "test-model-3"  # 0.9 factor
        inefficient_model = "test-model-2"  # 1.1 factor
        
        efficient_result = TokenCounter.count_tokens_for_model(text, efficient_model)
        inefficient_result = TokenCounter.count_tokens_for_model(text, inefficient_model)
        
        # Efficient model should produce fewer tokens
        assert efficient_result < inefficient_result
        
        # Verify the calculations
        assert efficient_result == int(base_count * 0.9)
        assert inefficient_result == int(base_count * 1.1)
