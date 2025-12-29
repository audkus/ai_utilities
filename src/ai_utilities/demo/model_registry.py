"""
Model registry for discovering and cataloging AI models.

Provides built-in cloud models and discovers local models from various servers.
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass

from typing import List, Optional, Dict, Any

import requests


MODEL_ID_PLACEHOLDER = "<model-id>"


class ProviderId(Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    GROQ = "groq"
    OLLAMA = "ollama"
    OPENAI_COMPAT_LOCAL = "openai_compatible_local"


@dataclass
class ModelDef:
    """Definition of an AI model."""
    provider: ProviderId
    display_name: str
    model: str
    base_url: str
    requires_env: Optional[str]
    is_local: bool
    endpoint_id: str


def get_builtin_cloud_models() -> List[ModelDef]:
    """Get curated cloud provider models.
    
    Returns:
        List of built-in cloud model definitions.
    """
    return [
        ModelDef(
            provider=ProviderId.OPENAI,
            display_name="OpenAI (cloud)",
            model="gpt-4o-mini",  # Modern default model
            base_url="https://api.openai.com/v1",
            requires_env="AI_API_KEY",
            is_local=False,
            endpoint_id="openai"
        ),
        ModelDef(
            provider=ProviderId.GROQ,
            display_name="Groq (cloud)",
            model="llama-3.1-8b-instant",
            base_url="https://api.groq.com/openai/v1",
            requires_env="GROQ_API_KEY",
            is_local=False,
            endpoint_id="groq"
        ),
    ]


def discover_ollama_models() -> List[ModelDef]:
    """Discover models from local Ollama server.
    
    Returns:
        List of Ollama model definitions.
    """
    models = []
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            data = response.json()
            for model_info in data.get("models", []):
                model_name = model_info.get("name", "")
                if model_name:
                    models.append(ModelDef(
                        provider=ProviderId.OLLAMA,
                        display_name="Ollama (local)",
                        model=model_info["name"],  # Keep full name with tag
                        base_url="http://localhost:11434/v1",
                        requires_env=None,
                        is_local=True,
                        endpoint_id="ollama"
                    ))
    except requests.RequestException:
        # Server not reachable - will be handled in validation
        pass
    
    # Always add at least one entry so user sees Ollama in menu
    if not models:
        models.append(ModelDef(
            provider=ProviderId.OLLAMA,
            display_name="Ollama (local)",
            model=MODEL_ID_PLACEHOLDER,
            base_url="http://localhost:11434/v1",
            requires_env=None,
            is_local=True,
            endpoint_id="ollama"
        ))
    
    return models


def discover_openai_compatible_models(endpoint_label: str, base_url: str) -> List[ModelDef]:
    """Discover models from an OpenAI-compatible server.
    
    Args:
        endpoint_label: Display name for the endpoint
        base_url: Base URL of the OpenAI-compatible server
        
    Returns:
        List of model definitions from the server.
    """
    models = []
    
    try:
        response = requests.get(f"{base_url}/models", timeout=2)
        if response.status_code == 200:
            data = response.json()
            for model_info in data.get("data", []):
                model_id = model_info.get("id")
                if model_id:
                    models.append(ModelDef(
                        provider=ProviderId.OPENAI_COMPAT_LOCAL,
                        display_name=endpoint_label,
                        model=model_id,
                        base_url=base_url,
                        requires_env=None,
                        is_local=True,
                        endpoint_id=endpoint_label.lower().replace(" ", "_").replace("(", "").replace(")", "")
                    ))
    except requests.RequestException:
        # Server not reachable - will be handled in validation
        pass
    
    # Always add at least one entry so user sees endpoint in menu
    if not models:
        models.append(ModelDef(
            provider=ProviderId.OPENAI_COMPAT_LOCAL,
            display_name=endpoint_label,
            model=MODEL_ID_PLACEHOLDER,
            base_url=base_url,
            requires_env=None,
            is_local=True,
            endpoint_id=endpoint_label.lower().replace(" ", "_").replace("(", "").replace(")", "")
        ))
    
    return models


def build_catalog() -> List[ModelDef]:
    """Build complete catalog of available models.
    
    Returns:
        List of all model definitions (cloud + local discovered).
    """
    # Start with built-in cloud models
    catalog = get_builtin_cloud_models()
    
    # Add Ollama models
    catalog.extend(discover_ollama_models())
    
    # Add local OpenAI-compatible endpoints (always present in catalog)
    local_endpoints = [
        ("FastChat (local)", "http://localhost:8000/v1"),
        ("LM Studio (local)", "http://localhost:1234/v1"),
        ("text-generation-webui (local)", "http://localhost:5000/v1"),
    ]
    
    for endpoint_label, base_url in local_endpoints:
        catalog.extend(discover_openai_compatible_models(endpoint_label, base_url))
    
    return catalog
