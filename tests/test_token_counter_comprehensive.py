"""
Comprehensive tests for token_counter.py module.
"""

import pytest
from unittest.mock import patch, MagicMock
from ai_utilities.token_counter import TokenCounter


class TestTokenCounter:
    """Comprehensive tests for TokenCounter class."""
    
    def test_class_constants(self):
        """Test class constants are properly defined."""
        assert TokenCounter.WORD_TO_TOKEN_RATIO == 0.75
        assert TokenCounter.CHAR_TO_TOKEN_RATIO == 4.0
        assert TokenCounter.MESSAGE_OVERHEAD == 4
        assert TokenCounter.ROLE_OVERHEAD == 2
    
    def test_count_tokens_empty_string(self):
        """Test token counting with empty string."""
        result = TokenCounter.count_tokens("")
        assert result == 0
        
        result = TokenCounter.count_tokens("   ")
        assert result == 0
        
        result = TokenCounter.count_tokens("\n\t")
        assert result == 0
    
    def test_count_tokens_word_method(self):
        """Test token counting using word method."""
        text = "This is a test sentence with seven words"
        result = TokenCounter.count_tokens(text, "word")
        
        # Let the actual implementation determine the result
        expected = TokenCounter._count_by_words(text)
        assert result == expected
    
    def test_count_tokens_char_method(self):
        """Test token counting using character method."""
        text = "This is a test"
        result = TokenCounter.count_tokens(text, "char")
        
        # 14 characters / 4.0 ratio = 3.5, rounded to int = 3
        expected = int(len(text) / TokenCounter.CHAR_TO_TOKEN_RATIO)
        assert result == expected
    
    def test_count_tokens_combined_method(self):
        """Test token counting using combined method."""
        text = "This is a test sentence"
        
        word_count = TokenCounter._count_by_words(text)
        char_count = TokenCounter._count_by_chars(text)
        combined_expected = int((word_count + char_count) / 2)
        
        result = TokenCounter.count_tokens(text, "combined")
        assert result == combined_expected
    
    def test_count_tokens_default_method(self):
        """Test token counting with default method."""
        text = "This is a test"
        
        result_default = TokenCounter.count_tokens(text)
        result_word = TokenCounter.count_tokens(text, "word")
        
        assert result_default == result_word
    
    def test_count_tokens_invalid_method(self):
        """Test token counting with invalid method."""
        text = "This is a test"
        
        with pytest.raises(ValueError, match="Unknown counting method: invalid"):
            TokenCounter.count_tokens(text, "invalid")
    
    def test_count_by_words_helper(self):
        """Test the _count_by_words helper method."""
        text = "word1 word2 word3"
        result = TokenCounter._count_by_words(text)
        expected = int(3 / TokenCounter.WORD_TO_TOKEN_RATIO)
        assert result == expected
        
        # Test with extra whitespace
        text_whitespace = "  word1   word2\tword3\n  "
        result_whitespace = TokenCounter._count_by_words(text_whitespace)
        assert result_whitespace == expected  # Should be same as whitespace is normalized by split()
    
    def test_count_by_chars_helper(self):
        """Test the _count_by_chars helper method."""
        text = "abcdef"
        result = TokenCounter._count_by_chars(text)
        expected = int(6 / TokenCounter.CHAR_TO_TOKEN_RATIO)
        assert result == expected
        
        # Test with whitespace
        text_whitespace = "abc def"
        result_whitespace = TokenCounter._count_by_chars(text_whitespace)
        expected_whitespace = int(7 / TokenCounter.CHAR_TO_TOKEN_RATIO)  # Including space
        assert result_whitespace == expected_whitespace
    
    def test_count_combined_helper(self):
        """Test the _count_combined helper method."""
        text = "test sentence"
        
        word_count = TokenCounter._count_by_words(text)
        char_count = TokenCounter._count_by_chars(text)
        combined_expected = int((word_count + char_count) / 2)
        
        result = TokenCounter._count_combined(text)
        assert result == combined_expected
    
    def test_count_message_tokens_empty_list(self):
        """Test counting tokens for empty message list."""
        result = TokenCounter.count_message_tokens([])
        assert result == 0
    
    def test_count_message_tokens_single_message(self):
        """Test counting tokens for single message."""
        messages = [{"role": "user", "content": "Hello world"}]
        
        content_tokens = TokenCounter.count_tokens("Hello world", "word")
        role_tokens = TokenCounter.count_tokens("user", "word")
        expected = content_tokens + role_tokens + TokenCounter.MESSAGE_OVERHEAD
        
        result = TokenCounter.count_message_tokens(messages, "word")
        assert result == expected
    
    def test_count_message_tokens_multiple_messages(self):
        """Test counting tokens for multiple messages."""
        messages = [
            {"role": "user", "content": "Hello world"},
            {"role": "assistant", "content": "Hi there! How can I help you?"}
        ]
        
        total_tokens = 0
        for message in messages:
            content_tokens = TokenCounter.count_tokens(message["content"], "word")
            role_tokens = TokenCounter.count_tokens(message["role"], "word")
            total_tokens += content_tokens + role_tokens + TokenCounter.MESSAGE_OVERHEAD
        
        result = TokenCounter.count_message_tokens(messages, "word")
        assert result == total_tokens
    
    def test_count_message_tokens_missing_fields(self):
        """Test counting tokens with missing message fields."""
        messages = [
            {"content": "Hello world"},  # Missing role
            {"role": "user"},  # Missing content
            {},  # Missing both
        ]
        
        result = TokenCounter.count_message_tokens(messages, "word")
        
        # Should handle missing fields gracefully
        assert result >= 0
        # Each message should have MESSAGE_OVERHEAD even with missing content/role
        expected_min = len(messages) * TokenCounter.MESSAGE_OVERHEAD
        assert result >= expected_min
    
    def test_count_message_tokens_different_methods(self):
        """Test message token counting with different methods."""
        messages = [{"role": "user", "content": "Hello world"}]
        
        result_word = TokenCounter.count_message_tokens(messages, "word")
        result_char = TokenCounter.count_message_tokens(messages, "char")
        result_combined = TokenCounter.count_message_tokens(messages, "combined")
        
        # All should be positive
        assert result_word > 0
        assert result_char > 0
        assert result_combined > 0
        
        # Results should be calculated correctly (they may be equal for short text)
        assert isinstance(result_word, int)
        assert isinstance(result_char, int)
        assert isinstance(result_combined, int)
    
    def test_count_message_tokens_logging(self):
        """Test that message token counting logs appropriately."""
        with patch('ai_utilities.token_counter.logger') as mock_logger:
            messages = [{"role": "user", "content": "Hello"}]
            
            TokenCounter.count_message_tokens(messages, "word")
            
            # Should log debug message
            mock_logger.debug.assert_called_once()
            assert "Estimated" in mock_logger.debug.call_args[0][0]
            assert "tokens" in mock_logger.debug.call_args[0][0]
    
    def test_estimate_response_tokens_basic(self):
        """Test basic response token estimation."""
        prompt_tokens = 100
        result = TokenCounter.estimate_response_tokens(prompt_tokens)
        
        # Should estimate response as 1.5x prompt (default factor)
        expected = int(prompt_tokens * 1.5)
        assert result == expected
        
        # Test with different factors
        result_half = TokenCounter.estimate_response_tokens(prompt_tokens, 0.5)
        expected_half = int(prompt_tokens * 0.5)
        assert result_half == expected_half
    
    def test_estimate_response_tokens_logging(self):
        """Test that response estimation logs appropriately."""
        with patch('ai_utilities.token_counter.logger') as mock_logger:
            TokenCounter.estimate_response_tokens(100, 1.5)
            
            # Should log debug message
            mock_logger.debug.assert_called_once()
            assert "Estimated" in mock_logger.debug.call_args[0][0]
            assert "response tokens" in mock_logger.debug.call_args[0][0]
    
    def test_count_tokens_for_model_basic(self):
        """Test model-specific token counting."""
        text = "This is a test"
        base_count = TokenCounter.count_tokens(text, "combined")
        
        # Test with known model
        result_known = TokenCounter.count_tokens_for_model(text, "gpt-3.5-turbo")
        assert isinstance(result_known, int)
        
        # Test with unknown model (should return base count)
        result_unknown = TokenCounter.count_tokens_for_model(text, "unknown-model")
        assert result_unknown == base_count
    
    def test_count_tokens_for_model_logging(self):
        """Test that model-specific counting logs appropriately."""
        with patch('ai_utilities.token_counter.logger') as mock_logger:
            text = "test"
            model = "test-model-1"
            
            TokenCounter.count_tokens_for_model(text, model)
            
            # Should log debug message
            mock_logger.debug.assert_called_once()
            log_message = mock_logger.debug.call_args[0][0]
            assert model in log_message
            assert "tokens" in log_message
    
    def test_count_tokens_for_model_basic(self):
        """Test model-specific token counting."""
        text = "This is a test"
        base_count = TokenCounter.count_tokens(text, "combined")
        
        result = TokenCounter.count_tokens_for_model(text, "unknown-model")
        assert result == base_count  # No adjustment for unknown model
    
    def test_count_tokens_for_model_known_models(self):
        """Test model-specific token counting for known models."""
        text = "This is a test"
        base_count = TokenCounter.count_tokens(text, "combined")
        
        # Test each known model
        model_tests = [
            ("test-model-1", 1.0),
            ("test-model-3", 0.9),
            ("test-model-2", 1.1),
            ("test-model-6", 1.1),
        ]
        
        for model, factor in model_tests:
            result = TokenCounter.count_tokens_for_model(text, model)
            expected = int(base_count * factor)
            assert result == expected, f"Failed for model {model}"
    
    def test_count_tokens_for_model_case_sensitivity(self):
        """Test model-specific token counting case sensitivity."""
        text = "test"
        
        result_lower = TokenCounter.count_tokens_for_model(text, "test-model-1")
        result_upper = TokenCounter.count_tokens_for_model(text, "Test-Model-1")
        result_mixed = TokenCounter.count_tokens_for_model(text, "TEST-MODEL-1")
        
        # Should be case sensitive - only exact match gets adjustment
        base_count = TokenCounter.count_tokens(text, "combined")
        assert result_lower == int(base_count * 1.0)  # Known model
        assert result_upper == base_count  # Unknown model
        assert result_mixed == base_count  # Unknown model
    
    @patch('ai_utilities.token_counter.logger')
    def test_count_tokens_for_model_logging(self, mock_logger):
        """Test that model-specific counting logs appropriately."""
        text = "test"
        model = "test-model-1"
        
        TokenCounter.count_tokens_for_model(text, model)
        
        # Should log debug message
        mock_logger.debug.assert_called_once()
        log_message = mock_logger.debug.call_args[0][0]
        assert model in log_message
        assert "tokens" in log_message
    
    def test_count_tokens_unicode_text(self):
        """Test token counting with unicode text."""
        unicode_text = "Hello 世界 café naïve résumé 🚀"
        
        result_word = TokenCounter.count_tokens(unicode_text, "word")
        result_char = TokenCounter.count_tokens(unicode_text, "char")
        result_combined = TokenCounter.count_tokens(unicode_text, "combined")
        
        # All should handle unicode gracefully
        assert result_word > 0
        assert result_char > 0
        assert result_combined > 0
        
        # Combined should be average of word and char
        expected_combined = int((result_word + result_char) / 2)
        assert result_combined == expected_combined
    
    def test_count_tokens_very_long_text(self):
        """Test token counting with very long text."""
        long_text = "word " * 1000  # 1000 words
        
        result = TokenCounter.count_tokens(long_text, "word")
        expected = int(1000 / TokenCounter.WORD_TO_TOKEN_RATIO)
        assert result == expected
        
        # Should be reasonable number
        assert result > 1000
        assert result < 2000
    
    def test_count_tokens_special_characters(self):
        """Test token counting with special characters."""
        special_text = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        
        result_word = TokenCounter.count_tokens(special_text, "word")
        result_char = TokenCounter.count_tokens(special_text, "char")
        
        # Word method should treat as one word
        expected_word = int(1 / TokenCounter.WORD_TO_TOKEN_RATIO)
        assert result_word == expected_word
        
        # Char method should count all characters
        expected_char = int(len(special_text) / TokenCounter.CHAR_TO_TOKEN_RATIO)
        assert result_char == expected_char
    
    def test_count_tokens_whitespace_variations(self):
        """Test token counting with various whitespace patterns."""
        texts = [
            "word1 word2 word3",
            "word1\tword2\nword3",
            "  word1   word2\tword3\n  ",
            "word1\n\nword2\r\nword3",
        ]
        
        results = [TokenCounter.count_tokens(text, "word") for text in texts]
        
        # All should produce the same result for word method
        # because split() normalizes whitespace
        assert all(r == results[0] for r in results)
    
    def test_count_tokens_performance_considerations(self):
        """Test that token counting is efficient."""
        import time
        
        large_text = "word " * 10000  # Large text
        
        start_time = time.time()
        result = TokenCounter.count_tokens(large_text, "word")
        end_time = time.time()
        
        # Should complete quickly
        assert end_time - start_time < 1.0
        assert result > 0
    
    def test_edge_cases_empty_and_none(self):
        """Test edge cases with empty and None inputs."""
        # Empty string
        assert TokenCounter.count_tokens("") == 0
        
        # String with only whitespace
        assert TokenCounter.count_tokens("   \t\n   ") == 0
        
        # Single character
        assert TokenCounter.count_tokens("a") > 0
        
        # Single word
        assert TokenCounter.count_tokens("hello") > 0
