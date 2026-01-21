"""
rate_limit_fetcher.py

Service for fetching OpenAI rate limits dynamically from the API.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from .config_models import ModelConfig

logger = logging.getLogger(__name__)


@dataclass
class RateLimitInfo:
    """Rate limit information for a specific model."""
    model_name: str
    requests_per_minute: int
    tokens_per_minute: int
    tokens_per_day: int
    last_updated: datetime

    def to_model_config(self) -> ModelConfig:
        """Convert to a valid ModelConfig (clamped to constraints)."""
        # ModelConfig constraints (keep in sync with ModelConfig validators)
        min_requests_per_minute: int = 1
        min_tokens_per_minute: int = 1000
        min_tokens_per_day: int = 10_000

        max_requests_per_minute: int = 10_000
        max_tokens_per_minute: int = 2_000_000
        max_tokens_per_day: int = 50_000_000

        rpm: int = max(min(self.requests_per_minute, max_requests_per_minute), min_requests_per_minute)
        tpm: int = max(min(self.tokens_per_minute, max_tokens_per_minute), min_tokens_per_minute)
        tpd: int = max(min(self.tokens_per_day, max_tokens_per_day), min_tokens_per_day)

        return ModelConfig(
            requests_per_minute=rpm,
            tokens_per_minute=tpm,
            tokens_per_day=tpd,
        )


class RateLimitFetcher:
    """
    Fetches and caches OpenAI rate limits from the API.
    
    Rate limits can be retrieved from OpenAI's API headers or through
    their management API. This service handles fetching, caching, and
    providing rate limit information.
    """
    
    def __init__(self, api_key: str, cache_dir: Optional[str] = None, cache_days: int = 30) -> None:
        """
        Initialize the rate limit fetcher.
        
        Args:
            api_key: OpenAI API key
            cache_dir: Directory to cache rate limit data
            cache_days: How many days to cache rate limit data (default 30 to match model checking)
        """
        self.api_key = api_key
        self.cache_dir = Path(cache_dir or Path.home() / ".ai_utilities" / "rate_limits")
        self.cache_days = cache_days
        self.cache_file = self.cache_dir / "openai_rate_limits.json"
        
        # Ensure cache directory exists
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            logger.warning(f"Failed to create cache directory {self.cache_dir}: {e}")
            # Fall back to a temporary directory
            import tempfile
            self.cache_dir = Path(tempfile.mkdtemp(prefix="ai_utilities_rate_limits_"))
            self.cache_file = self.cache_dir / "openai_rate_limits.json"
            logger.info(f"Using fallback cache directory: {self.cache_dir}")
        
        # Initialize OpenAI client
        from .openai_client import OpenAIClient
        self.client = OpenAIClient(api_key=api_key)
        
        logger.debug(f"RateLimitFetcher initialized with cache: {self.cache_file}")
    
    def get_rate_limits(self, force_refresh: bool = False) -> Dict[str, RateLimitInfo]:
        """
        Get rate limits for all available models.
        
        Args:
            force_refresh: Force refresh from API even if cache is valid
            
        Returns:
            Dictionary mapping model names to rate limit info
        """
        # Try to load from cache first
        if not force_refresh:
            cached_limits = self._load_from_cache()
            if cached_limits:
                logger.debug("Using cached rate limits")
                return cached_limits
        
        # Fetch from API
        logger.info("Fetching rate limits from OpenAI API")
        fresh_limits = self._fetch_from_api()
        
        # Save to cache
        self._save_to_cache(fresh_limits)
        
        return fresh_limits
    
    def get_model_rate_limit(self, model_name: str, force_refresh: bool = False) -> Optional[RateLimitInfo]:
        """
        Get rate limit for a specific model.
        
        Args:
            model_name: Name of the model
            force_refresh: Force refresh from API
            
        Returns:
            Rate limit info for the model or None if not found
        """
        all_limits = self.get_rate_limits(force_refresh=force_refresh)
        return all_limits.get(model_name)
    
    def _load_from_cache(self) -> Optional[Dict[str, RateLimitInfo]]:
        """Load rate limits from cache file."""
        try:
            if not self.cache_file.exists():
                return None
        except (OSError, PermissionError) as e:
            logger.warning(f"Cannot access cache file {self.cache_file}: {e}")
            return None
        
        try:
            with open(self.cache_file) as f:
                cache_data = json.load(f)
            
            # Check if cache is still valid
            last_updated = datetime.fromisoformat(cache_data.get('last_updated', '1970-01-01'))
            if datetime.now() - last_updated > timedelta(days=self.cache_days):
                logger.debug("Cache expired")
                return None
            
            # Parse cached rate limits
            limits = {}
            for model_name, limit_data in cache_data.get('models', {}).items():
                limits[model_name] = RateLimitInfo(
                    model_name=model_name,
                    requests_per_minute=limit_data['requests_per_minute'],
                    tokens_per_minute=limit_data['tokens_per_minute'],
                    tokens_per_day=limit_data['tokens_per_day'],
                    last_updated=datetime.fromisoformat(limit_data['last_updated'])
                )
            
            logger.debug(f"Loaded {len(limits)} rate limits from cache")
            return limits
            
        except Exception as e:
            logger.warning(f"Failed to load rate limits from cache: {e}")
            return None
    
    def _save_to_cache(self, limits: Dict[str, RateLimitInfo]) -> None:
        """Save rate limits to cache file."""
        try:
            cache_data = {
                'last_updated': datetime.now().isoformat(),
                'models': {}
            }
            
            for model_name, limit_info in limits.items():
                cache_data['models'][model_name] = {
                    'requests_per_minute': limit_info.requests_per_minute,
                    'tokens_per_minute': limit_info.tokens_per_minute,
                    'tokens_per_day': limit_info.tokens_per_day,
                    'last_updated': limit_info.last_updated.isoformat()
                }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.debug(f"Saved {len(limits)} rate limits to cache")
            
        except Exception as e:
            logger.warning(f"Failed to save rate limits to cache: {e}")
    
    def _fetch_from_api(self) -> Dict[str, RateLimitInfo]:
        """
        Fetch rate limits from OpenAI API.
        
        OpenAI provides rate limit information through:
        1. Response headers on API calls
        2. Management API endpoints
        3. Model-specific documentation
        
        This implementation uses a combination of these sources.
        """
        limits = {}
        
        # Method 1: Try to get from management API (if available)
        management_limits = self._fetch_from_management_api()
        if management_limits:
            limits.update(management_limits)
        
        # Method 2: Use known defaults for common models
        # These are based on OpenAI's published rate limits
        default_limits = self._get_known_rate_limits()
        limits.update(default_limits)
        
        # Method 3: Try to infer from API response headers
        # This is done by making a minimal API call and reading headers
        header_limits = self._fetch_from_response_headers()
        if header_limits:
            # Update existing limits with header information
            for model_name, header_limit in header_limits.items():
                if model_name in limits:
                    # Prefer API-provided limits over defaults
                    limits[model_name] = header_limit
                else:
                    limits[model_name] = header_limit
        
        logger.info(f"Fetched rate limits for {len(limits)} models")
        return limits
    
    def _fetch_from_management_api(self) -> Optional[Dict[str, RateLimitInfo]]:
        """
        Try to fetch rate limits from OpenAI's management API.
        
        Note: This endpoint may not be publicly available or may require
        special permissions. This is a best-effort implementation.
        """
        try:
            # OpenAI doesn't have a public rate limits management API
            # as of now, so this returns None
            # This is placeholder for future implementation if such API becomes available
            return None
            
        except Exception as e:
            logger.debug(f"Management API not available: {e}")
            return None
    
    def _get_known_rate_limits(self) -> Dict[str, RateLimitInfo]:
        """
        Get known rate limits for common OpenAI models.
        
        These are based on OpenAI's published documentation and may change
        over time. The dynamic fetching will update these when possible.
        """
        now = datetime.now()
        
        # Known rate limits based on OpenAI documentation
        # These are conservative estimates and may be updated by dynamic fetching
        known_limits = {
            "test-model-1": RateLimitInfo(
                model_name="test-model-1",
                requests_per_minute=5000,
                tokens_per_minute=450000,
                tokens_per_day=1350000,
                last_updated=now
            ),
            "test-model-4": RateLimitInfo(
                model_name="test-model-4",
                requests_per_minute=5000,
                tokens_per_minute=450000,
                tokens_per_day=1350000,
                last_updated=now
            ),
            "test-model-3": RateLimitInfo(
                model_name="test-model-3",
                requests_per_minute=5000,
                tokens_per_minute=500000,
                tokens_per_day=1500000,
                last_updated=now
            ),
            "test-model-5": RateLimitInfo(
                model_name="test-model-5",
                requests_per_minute=5000,
                tokens_per_minute=500000,
                tokens_per_day=1500000,
                last_updated=now
            ),
            "test-model-2": RateLimitInfo(
                model_name="test-model-2",
                requests_per_minute=5000,
                tokens_per_minute=2000000,
                tokens_per_day=20000000,
                last_updated=now
            ),
            "test-model-6": RateLimitInfo(
                model_name="test-model-6",
                requests_per_minute=5000,
                tokens_per_minute=2000000,
                tokens_per_day=20000000,
                last_updated=now
            ),
            "text-davinci-003": RateLimitInfo(
                model_name="text-davinci-003",
                requests_per_minute=3000,
                tokens_per_minute=3000000,
                tokens_per_day=90000000,
                last_updated=now
            ),
            "text-curie-001": RateLimitInfo(
                model_name="text-curie-001",
                requests_per_minute=3000,
                tokens_per_minute=3000000,
                tokens_per_day=90000000,
                last_updated=now
            ),
        }
        
        logger.debug(f"Using known rate limits for {len(known_limits)} models")
        return known_limits
    
    def _fetch_from_response_headers(self) -> Optional[Dict[str, RateLimitInfo]]:
        """
        Try to infer rate limits from API response headers.
        
        This makes a minimal API call and reads the rate limit headers
        to extract current rate limit information.
        """
        try:
            # Make a minimal API call to get rate limit headers
            response = self.client.create_chat_completion(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1
            )
            
            # Extract rate limit information from response headers
            # Note: The actual header names may vary and this is a best-effort approach
            headers = getattr(response, 'headers', {})
            
            # OpenAI typically includes rate limit headers like:
            # x-ratelimit-limit-requests: 5000
            # x-ratelimit-limit-tokens: 2000000
            # x-ratelimit-remaining-requests: 4999
            # x-ratelimit-remaining-tokens: 1999998
            
            rate_limits = {}
            
            # Try to extract rate limit information
            request_limit = headers.get('x-ratelimit-limit-requests')
            token_limit = headers.get('x-ratelimit-limit-tokens')
            
            if request_limit and token_limit:
                try:
                    rpm = int(request_limit)
                    tpm = int(token_limit)
                    
                    # Estimate daily limit (typically 30x the per-minute limit for tokens)
                    tpd = tpm * 30 * 24  # Conservative estimate
                    
                    # Determine model from the request
                    model_name = "gpt-3.5-turbo"  # From our test request
                    
                    rate_limits[model_name] = RateLimitInfo(
                        model_name=model_name,
                        requests_per_minute=rpm,
                        tokens_per_minute=tpm,
                        tokens_per_day=tpd,
                        last_updated=datetime.now()
                    )
                    
                    logger.debug(f"Inferred rate limits from headers for {model_name}")
                    
                except (ValueError, TypeError) as e:
                    logger.debug(f"Failed to parse rate limit headers: {e}")
            
            return rate_limits if rate_limits else None
            
        except Exception as e:
            logger.debug(f"Failed to fetch rate limits from response headers: {e}")
            return None
    
    def clear_cache(self) -> None:
        """Clear the rate limit cache."""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
                logger.debug("Rate limit cache cleared")
        except Exception as e:
            logger.warning(f"Failed to clear rate limit cache: {e}")
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get information about the cache status."""
        if not self.cache_file.exists():
            return {
                "cached": False,
                "cache_file": str(self.cache_file),
                "last_updated": None,
                "models_count": 0
            }
        
        try:
            with open(self.cache_file) as f:
                cache_data = json.load(f)
            
            last_updated = datetime.fromisoformat(cache_data.get('last_updated', '1970-01-01'))
            models_count = len(cache_data.get('models', {}))
            
            return {
                "cached": True,
                "cache_file": str(self.cache_file),
                "last_updated": last_updated.isoformat(),
                "models_count": models_count,
                "cache_age_days": (datetime.now() - last_updated).total_seconds() / 86400
            }
            
        except Exception as e:
            logger.warning(f"Failed to get cache status: {e}")
            return {
                "cached": False,
                "cache_file": str(self.cache_file),
                "last_updated": None,
                "models_count": 0,
                "error": str(e)
            }
