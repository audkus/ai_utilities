"""
token_counter.py

Token counting utilities with single responsibility for token estimation.
"""

import logging
from typing import List, Mapping, Any

logger = logging.getLogger(__name__)


class TokenCounter:
    """
    Handles token counting with single responsibility for estimation.
    
    This class only handles token counting and estimation. It doesn't
    make API calls, handle rate limiting, or process responses.
    """

    # Approximate token ratios for different content types
    WORD_TO_TOKEN_RATIO = 0.75  # Average tokens per word
    CHAR_TO_TOKEN_RATIO = 4.0   # Average characters per token
    
    # Special token counts
    MESSAGE_OVERHEAD = 4  # Approximate tokens per message wrapper
    ROLE_OVERHEAD = 2     # Approximate tokens for role markers

    @staticmethod
    def count_tokens(text: str, method: str = "word") -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to count tokens for
            method: Counting method ("word", "char", or "combined")
            
        Returns:
            Estimated token count
        """
        if not text:
            return 0
            
        if method == "word":
            return TokenCounter._count_by_words(text)
        elif method == "char":
            return TokenCounter._count_by_chars(text)
        elif method == "combined":
            return TokenCounter._count_combined(text)
        else:
            raise ValueError(f"Unknown counting method: {method}")

    @staticmethod
    def count_message_tokens(
        messages: List[dict[str, str]], 
        method: str = "word"
    ) -> int:
        """
        Estimate total tokens for a list of messages.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            method: Token counting method
            
        Returns:
            Total estimated tokens including message overhead
        """
        token_count: int = 0

        # Defensive normalization (avoid KeyError / None issues)
        safe_messages: List[Mapping[str, Any]] = [
            m if isinstance(m, dict) else {} for m in messages
        ]

        for msg in safe_messages:
            content: str = str(msg.get("content", "") or "")
            role: str = str(msg.get("role", "") or "")
            
            # Count content tokens using the proper token counting method
            content_tokens = TokenCounter.count_tokens(content, method)
            
            # Count role tokens using the proper token counting method
            role_tokens = TokenCounter.count_tokens(role, method)
            
            # Add message overhead
            token_count += content_tokens + role_tokens + TokenCounter.MESSAGE_OVERHEAD

        # Always log exactly once per call (matches your test expectation)
        logger.debug(
            "Estimated %d tokens for %d messages using %s method",
            token_count,
            len(safe_messages),
            method,
        )

        return token_count

    @staticmethod
    def _count_by_words(text: str) -> int:
        """Count tokens by word-based estimation."""
        words = text.split()
        return int(len(words) / TokenCounter.WORD_TO_TOKEN_RATIO)

    @staticmethod
    def _count_by_chars(text: str) -> int:
        """Count tokens by character-based estimation."""
        return int(len(text) / TokenCounter.CHAR_TO_TOKEN_RATIO)

    @staticmethod
    def _count_combined(text: str) -> int:
        """Count tokens using combined word and character estimation."""
        word_count = TokenCounter._count_by_words(text)
        char_count = TokenCounter._count_by_chars(text)
        
        # Average the two methods for better accuracy
        return int((word_count + char_count) / 2)

    @staticmethod
    def estimate_response_tokens(
        prompt_tokens: int, 
        response_length_factor: float = 1.5
    ) -> int:
        """
        Estimate response tokens based on prompt size.
        
        Args:
            prompt_tokens: Number of tokens in prompt
            response_length_factor: Multiplier for expected response length
            
        Returns:
            Estimated response token count
        """
        estimated = int(prompt_tokens * response_length_factor)
        logger.debug(f"Estimated {estimated} response tokens for {prompt_tokens} prompt tokens")
        return estimated

    @staticmethod
    def count_tokens_for_model(text: str, model: str = "gpt-3.5-turbo") -> int:
        """
        Count tokens with model-specific adjustments.
        
        Args:
            text: Text to count tokens for
            model: OpenAI model name for model-specific adjustments
            
        Returns:
            Model-adjusted token count
        """
        base_count = TokenCounter.count_tokens(text, "combined")
        
        # Model-specific adjustments (approximate)
        model_adjustments = {
            "test-model-1": 1.0,          # Standard
            "test-model-3": 0.9,    # More efficient
            "test-model-2": 1.1,  # Less efficient
            "test-model-6": 1.1,
        }
        
        adjustment = model_adjustments.get(model, 1.0)
        adjusted_count = int(base_count * adjustment)
        
        logger.debug(f"Model {model}: {base_count} -> {adjusted_count} tokens")
        return adjusted_count
