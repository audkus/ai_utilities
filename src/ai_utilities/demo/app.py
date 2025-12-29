"""
Main application orchestrator for the AI utilities demo.

Coordinates model discovery, validation, selection, and scenario execution.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional, Dict, Any

from .model_registry import MODEL_ID_PLACEHOLDER, build_catalog, ModelDef, ProviderId
from .validation import validate_model, ValidatedModel
from .menu import (
    render_model_menu, render_scenario_menu, prompt_model_choice, 
    prompt_scenario_choice, sort_models_alphabetically
)
from .scenarios import (
    SelectedModelContext, basic_chat_example, json_response_example,
    typed_response_example, real_world_examples, error_handling_examples,
    provider_comparison_example
)


def run_app(args: argparse.Namespace) -> None:
    """Run the interactive demo application.

    Args:
        args: Parsed CLI arguments.

    Returns:
        None.
    """
    _normalize_args(args)

    # Build and validate model catalog
    catalog = build_catalog()
    validated_models = [validate_model(model_def, debug=args.debug) for model_def in catalog]
    
    # Sort models alphabetically (case-insensitive)
    validated_models = sort_models_alphabetically(validated_models)
    
    # Handle --list-models flag
    if args.list_models:
        print_models_and_exit(validated_models)
    
    # Resolve initial model selection
    selected_model = resolve_initial_selection(validated_models, args)
    
    if selected_model is None:
        if args.non_interactive:
            print("❌ No READY model available in non-interactive mode.")
            _print_non_interactive_help(validated_models)
            sys.exit(1)
        # Interactive mode - show model selection menu
        selected_model = interactive_model_selection(validated_models, args)
    
    if selected_model is None:
        print("👋 No model selected. Exiting.")
        return
    
    # Run scenario loop
    run_scenario_loop(selected_model, validated_models, args)


def resolve_initial_selection(
    validated_models: List[ValidatedModel], 
    args: argparse.Namespace
) -> Optional[ValidatedModel]:
    """Resolve model selection using CLI/env precedence.

    Args:
        validated_models: Validated catalog.
        args: Parsed CLI args.

    Returns:
        The selected model if resolvable, else None.
    """
    # Priority 1: CLI arguments
    if args.provider and args.model:
        return find_model_by_params(
            validated_models,
            provider=args.provider,
            model=args.model,
            base_url=args.base_url,
        )
    
    # Priority 2: Endpoint convenience flag
    if args.endpoint:
        model_def = get_endpoint_defaults(args.endpoint)
        if model_def:
            validated = find_matching_validated_model(validated_models, model_def)
            if validated and validated.status.value == "ready":
                return validated
    
    # Priority 3: Environment variables
    env_provider = os.getenv("AI_PROVIDER")
    env_model = os.getenv("AI_MODEL")
    env_base_url = os.getenv("AI_BASE_URL")
    
    if env_provider and env_model:
        return find_model_by_params(validated_models, env_provider, env_model, env_base_url)
    
    # Priority 4: Auto-select first ready model in non-interactive mode
    if args.non_interactive:
        for model in validated_models:
            if model.status.value == "ready":
                return model
    
    return None


def find_model_by_params(
    validated_models: List[ValidatedModel],
    provider: str,
    model: str,
    base_url: Optional[str] = None
) -> Optional[ValidatedModel]:
    """Find a validated model by provider/model/base_url.

    Args:
        validated_models: Validated models to search.
        provider: Provider string.
        model: Model id.
        base_url: Optional base URL.

    Returns:
        The matching validated model if found.
    """
    for validated in validated_models:
        model_def = validated.model_def
        
        # Check provider match
        if provider != model_def.provider.value:
            continue
        
        # Check model match (allow partial matches for convenience)
        if model != MODEL_ID_PLACEHOLDER and model != model_def.model:
            if model not in model_def.model and model_def.model not in model:
                continue
        
        # Check base URL match if specified
        if base_url and base_url != model_def.base_url:
            continue
        
        return validated
    
    return None


def find_matching_validated_model(
    validated_models: List[ValidatedModel],
    target_model_def: ModelDef
) -> Optional[ValidatedModel]:
    """Find a validated model matching the target model definition.
    
    Args:
        validated_models: List of validated models to search.
        target_model_def: Target model definition to match.
        
    Returns:
        Matching validated model or None.
    """
    for validated in validated_models:
        model_def = validated.model_def
        
        if (model_def.provider == target_model_def.provider and
            model_def.base_url == target_model_def.base_url and
            (model_def.model == target_model_def.model or 
             target_model_def.model == MODEL_ID_PLACEHOLDER)):
            return validated
    
    return None


def get_endpoint_defaults(endpoint: str) -> Optional[ModelDef]:
    """Return a default ModelDef for a convenience endpoint selector.

    Args:
        endpoint: Endpoint key.

    Returns:
        A ModelDef if endpoint is known, else None.
    """
    endpoint_map = {
        "openai": ModelDef(
            provider=ProviderId.OPENAI,
            display_name="OpenAI (cloud)",
            model="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
            requires_env="AI_API_KEY",
            is_local=False,
            endpoint_id="openai"
        ),
        "groq": ModelDef(
            provider=ProviderId.GROQ,
            display_name="Groq (cloud)",
            model="llama3-8b-8192",
            base_url="https://api.groq.com/openai/v1",
            requires_env="GROQ_API_KEY",
            is_local=False,
            endpoint_id="groq"
        ),
        "ollama": ModelDef(
            provider=ProviderId.OLLAMA,
            display_name="Ollama (local)",
            model="llama3.2:latest",
            base_url="http://localhost:11434/v1",
            requires_env=None,
            is_local=True,
            endpoint_id="ollama"
        ),
        "lmstudio": ModelDef(
            provider=ProviderId.OPENAI_COMPAT_LOCAL,
            display_name="LM Studio (local)",
            model=MODEL_ID_PLACEHOLDER,
            base_url="http://localhost:1234/v1",
            requires_env=None,
            is_local=True,
            endpoint_id="lmstudio"
        ),
        "textgen": ModelDef(
            provider=ProviderId.OPENAI_COMPAT_LOCAL,
            display_name="text-generation-webui (local)",
            model=MODEL_ID_PLACEHOLDER,
            base_url="http://localhost:5000/v1",
            requires_env=None,
            is_local=True,
            endpoint_id="textgen"
        ),
        "fastchat": ModelDef(
            provider=ProviderId.OPENAI_COMPAT_LOCAL,
            display_name="FastChat (local)",
            model=MODEL_ID_PLACEHOLDER,
            base_url="http://localhost:8000/v1",
            requires_env=None,
            is_local=True,
            endpoint_id="fastchat"
        )
    }
    
    return endpoint_map.get(endpoint.lower())


def interactive_model_selection(
    validated_models: List[ValidatedModel],
    args: argparse.Namespace
) -> Optional[ValidatedModel]:
    """Interactive model selection loop.

    Args:
        validated_models: Validated model list.
        args: CLI args.

    Returns:
        A READY ValidatedModel, or None if user exits.
    """
    while True:
        render_model_menu(validated_models)
        choice = prompt_model_choice(validated_models)
        
        if choice is None:
            return None
        
        selected_model = validated_models[choice - 1]
        
        # Check if model is ready
        if selected_model.status.value == "ready":
            return selected_model
        
        # Show fix instructions and prompt for re-check
        print(f"\n❌ Model not ready: {selected_model.status_detail}")
        print(f"\n💡 Fix instructions:")
        print(selected_model.fix_instructions)
        
        try:
            input("\nPress Enter to re-check models...")
        except (KeyboardInterrupt, EOFError):
            return None
        
        # Re-validate models
        catalog = build_catalog()
        validated_models = [validate_model(model_def, debug=args.debug) for model_def in catalog]
        validated_models = sort_models_alphabetically(validated_models)


def run_scenario_loop(
    selected_model: ValidatedModel,
    all_models: List[ValidatedModel],
    args: argparse.Namespace
) -> None:
    """Run the scenario menu for a selected model.

    Args:
        selected_model: Selected model.
        all_models: All validated models.
        args: CLI args.

    Returns:
        None.
    """
    # Create model context
    ctx = SelectedModelContext(
        provider=_to_client_provider(selected_model.model_def.provider),
        model=selected_model.model_def.model,
        base_url=selected_model.model_def.base_url,
        endpoint_label=selected_model.model_def.display_name,
        required_env_vars_used=[selected_model.model_def.requires_env] if selected_model.model_def.requires_env else []
    )
    
    while True:
        render_scenario_menu(selected_model)
        choice = prompt_scenario_choice()
        
        if choice is None:
            break
        
        try:
            # Execute selected scenario
            if choice == 1:
                basic_chat_example(ctx)
            elif choice == 2:
                json_response_example(ctx)
            elif choice == 3:
                typed_response_example(ctx)
            elif choice == 4:
                provider_comparison_example(ctx, all_models)
            elif choice == 5:
                real_world_examples(ctx)
            elif choice == 6:
                error_handling_examples(ctx)
            elif choice == 7:
                # Re-validate selected model
                print("🔄 Re-validating selected model...")
                revalidated = validate_model(selected_model.model_def, debug=args.debug)
                if revalidated.status.value == "ready":
                    print("✅ Model is ready!")
                    selected_model = revalidated
                    ctx.model = selected_model.model_def.model
                else:
                    print(f"❌ Model validation failed: {revalidated.status_detail}")
                    print(revalidated.fix_instructions)
            elif choice == 8:
                # Change model - return to model selection
                new_model = interactive_model_selection(all_models, args)
                if new_model:
                    selected_model = new_model
                    ctx = SelectedModelContext(
                        provider=_to_client_provider(selected_model.model_def.provider),
                        model=selected_model.model_def.model,
                        base_url=selected_model.model_def.base_url,
                        endpoint_label=selected_model.model_def.display_name,
                        required_env_vars_used=[selected_model.model_def.requires_env] if selected_model.model_def.requires_env else []
                    )
            
            # Prompt to continue (unless exiting or changing model)
            if choice not in (0, 8):
                try:
                    input("\n🔄 Press Enter to continue...")
                except (KeyboardInterrupt, EOFError):
                    break
                    
        except Exception as e:
            if args.debug:
                import traceback
                traceback.print_exc()
            else:
                print(f"❌ Error running scenario: {e}")
            
            try:
                input("\n🔄 Press Enter to continue...")
            except (KeyboardInterrupt, EOFError):
                break
    
    print("👋 Thanks for using AI Utilities!")


def print_models_and_exit(validated_models: List[ValidatedModel]) -> None:
    """Print validated models list and exit.

    Args:
        validated_models: Validated models to print.

    Returns:
        None. Exits the process.
    """
    print("🤖 AI UTILITIES - AVAILABLE MODELS")
    print("=" * 50)
    
    for i, model in enumerate(validated_models, 1):
        status_icon = {"ready": "✅", "needs_key": "⚠", "unreachable": "❌", "invalid_model": "❌", "error": "❌"}.get(model.status.value, "❓")
        status_detail = model.status_detail
        
        print(f"[{i}] {model.menu_line_text} {status_icon} {status_detail}")
        
        if model.status.value != "ready" and model.fix_instructions:
            print(f"    💡 {model.fix_instructions.replace(chr(10), '; ')}")
    
    sys.exit(0)


def _normalize_args(args: argparse.Namespace) -> None:
    """Normalize CLI args to match provider_factory expectations.

    Args:
        args: Parsed CLI args.

    Returns:
        None.
    """
    if getattr(args, "provider", None) == "ollama":
        args.provider = "openai_compatible"
        if not getattr(args, "base_url", None):
            args.base_url = "http://localhost:11434/v1"


def _print_non_interactive_help(validated_models: List[ValidatedModel]) -> None:
    """Print actionable help for non-interactive failures.

    Args:
        validated_models: Validated models.

    Returns:
        None.
    """
    for model in validated_models:
        if model.status.value == "ready":
            continue
        if model.fix_instructions:
            print(f"\n- {model.menu_line_text}: {model.status_detail}")
            print(model.fix_instructions)


def _to_client_provider(provider_id: ProviderId) -> str:
    """Map ProviderId to ai_utilities provider string.

    Args:
        provider_id: Provider identifier.

    Returns:
        Provider string accepted by ai_utilities.create_client.
    """
    if provider_id == ProviderId.OPENAI:
        return "openai"

    return "openai_compatible"
