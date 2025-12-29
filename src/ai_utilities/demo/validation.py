"""
Model validation and status checking.

Validates model availability and provides actionable fix instructions.
"""

from __future__ import annotations

import os
import sys
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass

import requests

from ai_utilities import create_client

from .model_registry import MODEL_ID_PLACEHOLDER, ModelDef, ProviderId


class ModelStatus(Enum):
    """Model validation status."""
    READY = "ready"
    NEEDS_KEY = "needs_key"
    UNREACHABLE = "unreachable"
    INVALID_MODEL = "invalid_model"
    ERROR = "error"


@dataclass
class ValidatedModel:
    """A model with its validation status and metadata."""
    model_def: ModelDef
    status: ModelStatus
    status_detail: str
    fix_instructions: str
    menu_line_text: str


def validate_model(model_def: ModelDef, debug: bool = False) -> ValidatedModel:
    """Validate a model definition and return status with fix instructions.
    
    Args:
        model_def: Model definition to validate
        debug: Whether to include debug information
        
    Returns:
        ValidatedModel with status and instructions.
    """
    try:
        # Check environment variables for cloud providers
        if model_def.requires_env:
            env_value = os.getenv(model_def.requires_env)
            if not env_value or env_value == f"your-{model_def.requires_env.lower()}-here":
                return _create_needs_key_result(model_def)
        
        # Check server reachability for local providers
        if model_def.is_local:
            if not _is_server_reachable(model_def.base_url, debug):
                return _create_unreachable_result(model_def)
        
        # Validate model existence. Placeholder entries require explicit model.
        if model_def.model == MODEL_ID_PLACEHOLDER:
            return _create_invalid_model_result(model_def)

        if not _is_model_available(model_def, debug):
            return _create_invalid_model_result(model_def)
        
        # Model is ready
        return _create_ready_result(model_def)
        
    except Exception as e:
        if debug:
            print(f"Debug: Unexpected error validating {model_def.display_name}: {e}", file=sys.stderr)
        return _create_error_result(model_def, str(e))


def _create_needs_key_result(model_def: ModelDef) -> ValidatedModel:
    """Create result for missing API key."""
    if model_def.requires_env == "AI_API_KEY":
        instructions = (
            "Get your OpenAI API key from https://platform.openai.com/api-keys\n"
            "Add to your .env file:\n"
            "AI_API_KEY=sk-your-openai-key-here"
        )
    elif model_def.requires_env == "GROQ_API_KEY":
        instructions = (
            "Get your Groq API key from https://console.groq.com/\n"
            "Add to your .env file:\n"
            "GROQ_API_KEY=gsk_your-groq-key-here"
        )
    else:
        instructions = f"Set environment variable: {model_def.requires_env}"
    
    menu_text = _build_menu_line_text(model_def)
    
    return ValidatedModel(
        model_def=model_def,
        status=ModelStatus.NEEDS_KEY,
        status_detail="missing API key",
        fix_instructions=instructions,
        menu_line_text=menu_text
    )


def _create_unreachable_result(model_def: ModelDef) -> ValidatedModel:
    """Create result for unreachable server."""
    if "ollama" in model_def.base_url:
        instructions = (
            "Start Ollama server:\n"
            "  ollama serve\n"
            f"Expected URL: {model_def.base_url}"
        )
    elif "1234" in model_def.base_url:  # LM Studio
        instructions = (
            "Start LM Studio and enable server:\n"
            "  1. Open LM Studio\n"
            "  2. Go to the 'Server' tab\n"
            "  3. Click 'Start Server'\n"
            f"Expected URL: {model_def.base_url}"
        )
    elif "5000" in model_def.base_url:  # text-generation-webui
        instructions = (
            "Start text-generation-webui with API:\n"
            "  python server.py --api\n"
            f"Expected URL: {model_def.base_url}"
        )
    elif "8000" in model_def.base_url:  # FastChat
        instructions = (
            "Start FastChat controller:\n"
            "  python3 -m fastchat.serve.controller\n"
            f"Expected URL: {model_def.base_url}"
        )
    else:
        instructions = f"Start server at: {model_def.base_url}"
    
    menu_text = _build_menu_line_text(model_def)
    
    return ValidatedModel(
        model_def=model_def,
        status=ModelStatus.UNREACHABLE,
        status_detail="server not running",
        fix_instructions=instructions,
        menu_line_text=menu_text
    )


def _create_invalid_model_result(model_def: ModelDef) -> ValidatedModel:
    """Create result for invalid/missing model."""
    if model_def.model == MODEL_ID_PLACEHOLDER:
        instructions = (
            "Model id is not known for this endpoint.\n"
            "Provide a model with one of:\n"
            "  - --model <model-id>\n"
            "  - AI_MODEL=<model-id>\n"
            "Then re-validate."
        )
    elif model_def.provider == ProviderId.OLLAMA:
        instructions = (
            f"Pull the model in Ollama:\n"
            f"  ollama pull {model_def.model}"
        )
    else:
        instructions = (
            f"Model '{model_def.model}' not found on server.\n"
            f"Check available models or specify a valid model ID."
        )
    
    menu_text = _build_menu_line_text(model_def)
    
    return ValidatedModel(
        model_def=model_def,
        status=ModelStatus.INVALID_MODEL,
        status_detail="model not found",
        fix_instructions=instructions,
        menu_line_text=menu_text
    )


def _create_ready_result(model_def: ModelDef) -> ValidatedModel:
    """Create result for ready model."""
    menu_text = _build_menu_line_text(model_def)
    
    return ValidatedModel(
        model_def=model_def,
        status=ModelStatus.READY,
        status_detail="ready",
        fix_instructions="",
        menu_line_text=menu_text
    )


def _create_error_result(model_def: ModelDef, error_msg: str) -> ValidatedModel:
    """Create result for unexpected error."""
    menu_text = _build_menu_line_text(model_def)
    
    return ValidatedModel(
        model_def=model_def,
        status=ModelStatus.ERROR,
        status_detail="unexpected error",
        fix_instructions=f"Error: {error_msg}",
        menu_line_text=menu_text
    )


def _is_server_reachable(base_url: str, debug: bool = False) -> bool:
    """Check if server at base_url is reachable.
    
    Args:
        base_url: Base URL to check
        debug: Whether to print debug info
        
    Returns:
        True if server is reachable.
    """
    try:
        # Try to reach the server's models endpoint or root
        if base_url.endswith("/v1"):
            health_url = base_url.replace("/v1", "/v1/models")
        else:
            health_url = f"{base_url}/v1/models"
            
        response = requests.get(health_url, timeout=2)
        if debug:
            print(f"Debug: Server check {health_url} -> {response.status_code}", file=sys.stderr)
        return response.status_code in (200, 401)  # 401 means server is up but needs auth
    except requests.RequestException as e:
        if debug:
            print(f"Debug: Server check failed: {e}", file=sys.stderr)
        return False


def _is_model_available(model_def: ModelDef, debug: bool = False) -> bool:
    """Check if the specific model is available on the server.
    
    Args:
        model_def: Model definition to check
        debug: Whether to print debug info
        
    Returns:
        True if model is available.
    """
    # Placeholder models cannot be validated without user input.
    if model_def.model == MODEL_ID_PLACEHOLDER:
        return False

    # Do a minimal test request to confirm model works.
    try:
        if model_def.provider == ProviderId.OPENAI:
            client = create_client(provider="openai", model=model_def.model, show_progress=False)
            _ = client.ask("ping", max_tokens=1)
            return True

        api_key = _get_local_api_key(model_def)
        client = create_client(
            provider="openai_compatible",
            base_url=model_def.base_url,
            api_key=api_key,
            show_progress=False,
        )
        _ = client.ask("ping", max_tokens=1, model=model_def.model)
        return True
    except Exception as e:
        if debug:
            print(f"Debug: Model test failed for {model_def.model}: {e}", file=sys.stderr)
        return False


def _get_local_api_key(model_def: ModelDef) -> str:
    """Resolve API key for local OpenAI-compatible endpoints."""
    if model_def.provider == ProviderId.GROQ:
        return os.getenv("GROQ_API_KEY", "")

    return os.getenv("LOCAL_OPENAI_API_KEY", "EMPTY")


def _build_menu_line_text(model_def: ModelDef) -> str:
    """Build the stable display text used for sorting and rendering."""
    if model_def.provider == ProviderId.OPENAI and model_def.model == "gpt-4o-mini":
        return f"{model_def.display_name} – <default>"

    return f"{model_def.display_name} – {model_def.model}"
