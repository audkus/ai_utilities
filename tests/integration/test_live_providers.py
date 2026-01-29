"""
Integration tests for live AI providers.

Tests actual connectivity to OpenAI, Groq, Ollama, LM Studio, text-generation-webui, and FastChat.
These tests are skipped unless RUN_LIVE_AI_TESTS=1 is set.
"""

from __future__ import annotations

import os
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock

import pytest

from ai_utilities import AiClient, AiSettings, create_client
from ai_utilities.providers.provider_capabilities import ProviderCapabilities


def get_actual_tgwui_url():
    """Get the actual TEXT_GENERATION_WEBUI_BASE_URL from environment."""
    return os.getenv("TEXT_GENERATION_WEBUI_BASE_URL", "http://localhost:5000/v1")


class TestLiveProviders:
    """Test live connectivity to AI providers."""

    @pytest.mark.integration
    @pytest.mark.openai
    def test_openai_live(self) -> None:
        """Test live OpenAI connectivity."""
        # Load .env file from repository root (pytest changes working directory)
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            
            # Get repository root (conftest.py is in tests/, so parent.parent is repo root)
            repo_root = Path(__file__).parent.parent
            env_file = repo_root / ".env"
            
            if env_file.exists():
                load_dotenv(env_file)
        except ImportError:
            pass  # dotenv not available
        
        # Check if live tests are enabled
        if os.getenv("RUN_LIVE_AI_TESTS") != "1":
            pytest.skip("Integration tests require RUN_LIVE_AI_TESTS=1")
        
        # Check if API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        model = os.getenv("LIVE_OPENAI_MODEL", "gpt-3.5-turbo")
        
        settings = AiSettings(
            provider="openai",
            api_key=api_key,
            model=model
        )
        client = AiClient(settings)

        # Minimal test call
        response = client.ask(
            "Reply with: pong",
            max_tokens=5,
            temperature=0.0
        )

        assert isinstance(response, str)
        assert len(response.strip()) > 0
        # Check that we got a reasonable response (not an error)
        assert response.strip().lower() in ["pong", "ping", "pong.", "ping."]

    @pytest.mark.integration
    @pytest.mark.groq
    def test_groq_live(self) -> None:
        """Test live Groq connectivity."""
        # Load .env file (pytest changes working directory)
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            
            # Get repository root (this file is in tests/, so parent.parent is repo root)
            repo_root = Path(__file__).parent.parent
            env_file = repo_root / ".env"
            
            if env_file.exists():
                load_dotenv(env_file)
        except ImportError:
            pass  # dotenv not available
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            pytest.skip("GROQ_API_KEY not set")

        model = os.getenv("LIVE_GROQ_MODEL", "llama-3.1-8b-instant")
        
        settings = AiSettings(
            provider="openai_compatible",
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key,
            model=model
        )
        client = AiClient(settings)

        response = client.ask(
            "Reply with: pong",
            max_tokens=5,
            temperature=0.0
        )

        assert isinstance(response, str)
        assert len(response.strip()) > 0
        assert "pong" in response.lower()

    @pytest.mark.integration
    @pytest.mark.ollama
    def test_ollama_live(self) -> None:
        """Test live Ollama connectivity."""
        base_url = os.getenv("LIVE_OLLAMA_URL", "http://localhost:11434/v1")
        model = os.getenv("LIVE_OLLAMA_MODEL", "llama3.2:latest")

        # Check if server is reachable
        if not self._is_server_reachable(base_url):
            pytest.skip(f"Ollama server not reachable at {base_url}")

        settings = AiSettings(
            provider="openai_compatible",
            base_url=base_url,
            api_key="dummy-key",  # Not required for Ollama
            model=model
        )
        client = AiClient(settings)

        response = client.ask(
            "Reply with: pong",
            max_tokens=5,
            temperature=0.0
        )

        assert isinstance(response, str)
        assert len(response.strip()) > 0

    @pytest.mark.integration
    @pytest.mark.lmstudio
    def test_lmstudio_live(self) -> None:
        """Test live LM Studio connectivity."""
        # Load .env file (pytest changes working directory)
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            
            # Get repository root (this file is in tests/, so parent.parent is repo root)
            repo_root = Path(__file__).parent.parent
            env_file = repo_root / ".env"
            
            if env_file.exists():
                load_dotenv(env_file)
        except ImportError:
            pass  # dotenv not available
        
        base_url = os.getenv("LIVE_LMSTUDIO_URL", "http://localhost:1234/v1")
        model = os.getenv("LIVE_LMSTUDIO_MODEL")

        if not model:
            pytest.skip("LIVE_LMSTUDIO_MODEL not set")

        # Check if server is reachable
        if not self._is_server_reachable(base_url):
            pytest.skip(f"LM Studio server not reachable at {base_url}")

        settings = AiSettings(
            provider="openai_compatible",
            base_url=base_url,
            api_key="dummy-key",
            model=model
        )
        client = AiClient(settings)

        response = client.ask(
            "Reply with: pong",
            max_tokens=5,
            temperature=0.0
        )

        assert isinstance(response, str)
        assert len(response.strip()) > 0

    @pytest.mark.integration
    @pytest.mark.text_generation_webui
    def test_textgen_live(self) -> None:
        """Test live Text Generation WebUI connectivity."""
        # Load .env file (pytest changes working directory)
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            
            # Get repository root (this file is in tests/, so parent.parent is repo root)
            repo_root = Path(__file__).parent.parent
            env_file = repo_root / ".env"
            
            if env_file.exists():
                load_dotenv(env_file)
        except ImportError:
            pass  # dotenv not available
        
        base_url = os.getenv("TEXT_GENERATION_WEBUI_URL", "http://127.0.0.1:7860/v1")
        model = os.getenv("LIVE_TEXTGEN_MODEL")

        if not model:
            pytest.skip("LIVE_TEXTGEN_MODEL not set")

        # Check if server is reachable
        if not self._is_server_reachable(base_url):
            pytest.skip(f"text-generation-webui server not reachable at {base_url}")

        settings = AiSettings(
            provider="openai_compatible",
            base_url=base_url,
            api_key="dummy-key",
            model=model
        )
        client = AiClient(settings)

        response = client.ask(
            "Reply with: pong",
            max_tokens=5,
            temperature=0.0
        )

        assert isinstance(response, str)
        assert len(response.strip()) > 0

    @pytest.mark.integration
    @pytest.mark.fastchat
    def test_fastchat_live(self) -> None:
        """Test live FastChat connectivity."""
        # Load .env file (pytest changes working directory)
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            
            # Get repository root (this file is in tests/, so parent.parent is repo root)
            repo_root = Path(__file__).parent.parent
            env_file = repo_root / ".env"
            
            if env_file.exists():
                load_dotenv(env_file)
        except ImportError:
            pass  # dotenv not available
        
        base_url = os.getenv("FASTCHAT_URL", "http://localhost:8000/v1")
        model = os.getenv("LIVE_FASTCHAT_MODEL")

        if not model:
            pytest.skip("LIVE_FASTCHAT_MODEL not set")

        # Check if server is reachable
        if not self._is_server_reachable(base_url):
            pytest.skip(f"FastChat server not reachable at {base_url}")

        settings = AiSettings(
            provider="openai_compatible",
            base_url=base_url,
            api_key="dummy-key",
            model=model
        )
        client = AiClient(settings)

        response = client.ask(
            "Reply with: pong",
            max_tokens=5,
            temperature=0.0
        )

        assert isinstance(response, str)
        assert len(response.strip()) > 0

    @pytest.mark.integration
    def test_create_client_function(self) -> None:
        """Test the create_client convenience function."""
        # Load .env file (pytest changes working directory)
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            
            # Get repository root (this file is in tests/, so parent.parent is repo root)
            repo_root = Path(__file__).parent.parent
            env_file = repo_root / ".env"
            
            if env_file.exists():
                load_dotenv(env_file)
        except ImportError:
            pass  # dotenv not available
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set for create_client test")

        # Test create_client with minimal parameters
        client = create_client(
            api_key=api_key,
            model="gpt-3.5-turbo",
            show_progress=False
        )

        response = client.ask(
            "Reply with: pong",
            max_tokens=5,
            temperature=0.0
        )

        assert isinstance(response, str)
        assert len(response.strip()) > 0

    @pytest.mark.integration
    def test_json_response_format(self) -> None:
        """Test JSON response format with live provider."""
        # Load .env file (pytest changes working directory)
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            
            # Get repository root (this file is in tests/, so parent.parent is repo root)
            repo_root = Path(__file__).parent.parent
            env_file = repo_root / ".env"
            
            if env_file.exists():
                load_dotenv(env_file)
        except ImportError:
            pass  # dotenv not available
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set for JSON test")

        client = create_client(api_key=api_key, model="gpt-3.5-turbo")

        response = client.ask(
            'Return JSON: {"status": "ok"}',
            return_format="json",
            max_tokens=50,
            temperature=0.0
        )

        # Should be parsed JSON
        assert isinstance(response, (dict, list))
        if isinstance(response, dict):
            assert "status" in response

    @pytest.mark.integration
    def test_batch_prompts(self) -> None:
        """Test batch prompts with live provider."""
        # Load .env file (pytest changes working directory)
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            
            # Get repository root (this file is in tests/, so parent.parent is repo root)
            repo_root = Path(__file__).parent.parent
            env_file = repo_root / ".env"
            
            if env_file.exists():
                load_dotenv(env_file)
        except ImportError:
            pass  # dotenv not available
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set for batch test")

        client = create_client(api_key=api_key, model="gpt-3.5-turbo")

        prompts = ["Reply with: 1", "Reply with: 2", "Reply with: 3"]
        responses = client.ask(
            prompts,
            max_tokens=5,
            temperature=0.0
        )

        assert isinstance(responses, list)
        assert len(responses) == 3
        for response in responses:
            assert isinstance(response, str)
            assert len(response.strip()) > 0

    @pytest.mark.integration
    @pytest.mark.together
    def test_together_live(self) -> None:
        """Test live Together AI connectivity."""
        api_key = os.getenv("TOGETHER_API_KEY")
        if not api_key:
            pytest.skip("TOGETHER_API_KEY not set")
        
        from ai_utilities import create_client
        
        client = create_client(
            provider="openai_compatible",
            base_url="https://api.together.xyz/v1",
            api_key=api_key,
            model="meta-llama/Llama-3.2-3B-Instruct-Turbo",
            show_progress=False
        )
        
        response = client.ask(
            "Hello! Please respond with just: Together AI is working!",
            max_tokens=10,
            temperature=0.1
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "Together AI" in response or "working" in response.lower()

    @pytest.mark.integration
    @pytest.mark.openrouter
    def test_openrouter_live(self) -> None:
        """Test live OpenRouter connectivity."""
        # Load .env file (pytest changes working directory)
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            
            # Get repository root (this file is in tests/, so parent.parent is repo root)
            repo_root = Path(__file__).parent.parent
            env_file = repo_root / ".env"
            
            if env_file.exists():
                load_dotenv(env_file)
        except ImportError:
            pass  # dotenv not available
        
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            pytest.skip("OPENROUTER_API_KEY not set")
        
        from ai_utilities import create_client
        
        # Try a different model that might be less rate-limited
        client = create_client(
            provider="openai_compatible",
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model="meta-llama/llama-3.2-1b-instruct:free",
            show_progress=False
        )
        
        try:
            response = client.ask(
                "Hello! Please respond with just: OpenRouter is working!",
                max_tokens=10,
                temperature=0.1
            )
            
            assert isinstance(response, str)
            assert len(response) > 0
            assert "OpenRouter" in response or "working" in response.lower()
            
        except Exception as e:
            # If rate limited, try a different approach
            if "rate limit" in str(e).lower() or "429" in str(e):
                # Just test that the connection works with a minimal request
                response = client.ask("Hi", max_tokens=2, temperature=0.1)
                assert isinstance(response, str)
                assert len(response) > 0
            else:
                raise

    def _is_server_reachable(self, base_url: str) -> bool:
        """Check if a server is reachable."""
        try:
            import requests
            response = requests.get(f"{base_url}/models", timeout=2)
            # Accept any response - server is reachable if it responds at all
            return True
        except Exception:
            return False


class TestProviderDiscovery:
    """Test live provider discovery functionality."""

    @pytest.mark.integration
    @pytest.mark.ollama
    def test_discover_ollama_models_live(self) -> None:
        """Test live Ollama model discovery."""
        base_url = os.getenv("LIVE_OLLAMA_URL", "http://localhost:11434/v1")

        if not self._is_server_reachable(base_url):
            pytest.skip(f"Ollama server not reachable at {base_url}")

        from ai_utilities.demo import get_demo_models
        
        models = get_demo_models("ollama")
        
        assert isinstance(models, list)
        if models:  # If server has models
            assert all(hasattr(m, 'id') for m in models)
            assert all(hasattr(m, 'name') for m in models)

    @pytest.mark.integration
    @pytest.mark.together
    def test_discover_together_models_live(self) -> None:
        """Test live Together AI model discovery."""
        # Load .env file (pytest changes working directory)
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            
            # Get repository root (this file is in tests/, so parent.parent is repo root)
            repo_root = Path(__file__).parent.parent
            env_file = repo_root / ".env"
            
            if env_file.exists():
                load_dotenv(env_file)
        except ImportError:
            pass  # dotenv not available
        
        api_key = os.getenv("TOGETHER_API_KEY")
        if not api_key:
            pytest.skip("TOGETHER_API_KEY not set")
        
        if not self._is_server_reachable("https://api.together.xyz/v1"):
            pytest.skip("Together AI server not reachable")
        
        from ai_utilities.demo import get_demo_models
        
        models = get_demo_models("together")
        
        assert isinstance(models, list)
        if models:  # If we have models
            assert all(hasattr(m, 'id') for m in models)
            assert all(hasattr(m, 'name') for m in models)

    @pytest.mark.integration
    @pytest.mark.openrouter
    def test_discover_openrouter_models_live(self) -> None:
        """Test live OpenRouter model discovery."""
        # Load .env file (pytest changes working directory)
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            
            # Get repository root (this file is in tests/, so parent.parent is repo root)
            repo_root = Path(__file__).parent.parent
            env_file = repo_root / ".env"
            
            if env_file.exists():
                load_dotenv(env_file)
        except ImportError:
            pass  # dotenv not available
        
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            pytest.skip("OPENROUTER_API_KEY not set")
        
        if not self._is_server_reachable("https://openrouter.ai/api/v1"):
            pytest.skip("OpenRouter server not reachable")
        
        from ai_utilities.demo import get_demo_models
        
        models = get_demo_models("text-generation-webui")
        
        assert isinstance(models, list)
        if models:  # If we have models
            assert all(hasattr(m, 'id') for m in models)
            assert all(hasattr(m, 'name') for m in models)

    @pytest.mark.integration
    @pytest.mark.lmstudio
    def test_discover_lmstudio_models_live(self) -> None:
        """Test live LM Studio model discovery."""
        base_url = os.getenv("LIVE_LMSTUDIO_URL", "http://localhost:1234/v1")

        if not self._is_server_reachable(base_url):
            pytest.skip(f"LM Studio server not reachable at {base_url}")

        from ai_utilities.demo import get_demo_models
        
        models = get_demo_models("lmstudio")
        
        assert isinstance(models, list)
        if models:  # If we have models
            assert all(hasattr(m, 'id') for m in models)
            assert all(hasattr(m, 'name') for m in models)

    @pytest.mark.integration
    @pytest.mark.text_generation_webui
    def test_discover_text_generation_webui_models_live(self) -> None:
        """Test live text-generation-webui model discovery."""
        base_url = os.getenv("TEXT_GENERATION_WEBUI_URL", "http://127.0.0.1:7860/v1")
        
        if not self._is_server_reachable(base_url):
            pytest.skip(f"Text-Generation-WebUI server not reachable at {base_url}")

        from ai_utilities.demo import get_demo_models
        
        models = get_demo_models("text-generation-webui")
        
        assert isinstance(models, list)
        if models:  # If we have models
            assert all(hasattr(m, 'id') for m in models)
            assert all(hasattr(m, 'name') for m in models)

    @pytest.mark.integration
    @pytest.mark.fastchat
    def test_discover_fastchat_models_live(self) -> None:
        """Test live FastChat model discovery."""
        base_url = os.getenv("FASTCHAT_URL", "http://localhost:8000/v1")
        
        if not self._is_server_reachable(base_url):
            pytest.skip(f"FastChat server not reachable at {base_url}")

        from ai_utilities.demo import get_demo_models
        
        models = get_demo_models("fastchat")
        
        assert isinstance(models, list)
        if models:  # If we have models
            assert all(hasattr(m, 'id') for m in models)
            assert all(hasattr(m, 'name') for m in models)

    def _is_server_reachable(self, base_url: str) -> bool:
        """Check if a server is reachable."""
        try:
            import requests
            response = requests.get(f"{base_url}/models", timeout=2)
            return True
        except Exception:
            return False


class TestValidationLive:
    """Test validation with live providers."""

    @pytest.mark.integration
    @pytest.mark.openai
    def test_validate_openai_live(self) -> None:
        """Test validation with live OpenAI."""
        # Load .env file (pytest changes working directory)
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            
            # Get repository root (this file is in tests/, so parent.parent is repo root)
            repo_root = Path(__file__).parent.parent
            env_file = repo_root / ".env"
            
            if env_file.exists():
                load_dotenv(env_file)
        except ImportError:
            pass  # dotenv not available
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        from ai_utilities.demo import validate_demo_model
        
        result = validate_demo_model("openai", "gpt-4o")
        
        assert result["valid"] is True
        assert result["provider"] == "openai"
        assert result["model_id"] == "gpt-4o"

    def _is_server_reachable(self, base_url: str) -> bool:
        """Check if a server is reachable."""
        try:
            import requests
            response = requests.get(f"{base_url}/models", timeout=2)
            return True
        except Exception:
            return False
