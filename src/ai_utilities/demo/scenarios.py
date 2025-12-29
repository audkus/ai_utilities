"""
Demo scenarios for testing AI functionality.

Each scenario runs with a selected model context.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Dict, Any

from pydantic import BaseModel

from ai_utilities import create_client, JsonParseError

if TYPE_CHECKING:
    from .validation import ValidatedModel


@dataclass
class SelectedModelContext:
    """Selected model configuration.

    Attributes:
        provider: Provider string accepted by `create_client`.
        model: Model identifier.
        base_url: Base URL for OpenAI-compatible endpoints.
        endpoint_label: Human-friendly label.
        required_env_vars_used: Environment variables relevant for this model.
    """
    provider: str
    model: str
    base_url: str
    endpoint_label: str
    required_env_vars_used: List[str]


class Person(BaseModel):
    """Example Pydantic model for typed responses."""
    name: str
    age: int
    email: Optional[str] = None


def basic_chat_example(ctx: SelectedModelContext) -> None:
    """Run a simple prompt and print the response.

    Args:
        ctx: Selected model context.

    Returns:
        None.
    """
    print("\n" + "="*60)
    print("💬 BASIC CHAT EXAMPLE")
    print("="*60)
    print("This is the simplest way to use the AI utilities library.\n")
    
    try:
        question = "What is Python? Explain in one sentence."
        print(f"👤 Question: {question}")

        if ctx.provider == "openai":
            client = create_client(provider="openai", model=ctx.model)
            response = client.ask(question)
        else:
            api_key = os.getenv("LOCAL_OPENAI_API_KEY", "EMPTY")
            client = create_client(
                provider="openai_compatible",
                base_url=ctx.base_url,
                api_key=api_key,
            )
            response = client.ask(question, model=ctx.model)

        print(f"🤖 AI Response: {response}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Check that the model is available and properly configured.")


def json_response_example(ctx: SelectedModelContext) -> None:
    """Request JSON and print parsed output.

    Args:
        ctx: Selected model context.

    Returns:
        None.
    """
    print("\n" + "="*60)
    print("📋 JSON RESPONSE EXAMPLE")
    print("="*60)
    print("Get structured data back from the AI.\n")
    
    try:
        prompt = "List 3 programming languages with their typical use cases"
        print(f"👤 Question: {prompt}")

        if ctx.provider == "openai":
            client = create_client(provider="openai", model=ctx.model)
            response = client.ask_json(prompt)
        else:
            api_key = os.getenv("LOCAL_OPENAI_API_KEY", "EMPTY")
            client = create_client(
                provider="openai_compatible",
                base_url=ctx.base_url,
                api_key=api_key,
            )
            response = client.ask_json(prompt, model=ctx.model)

        print(f"📊 JSON Response: {response}")
        
        # Access data programmatically
        if isinstance(response, list):
            print(f"📈 Found {len(response)} items")
            for i, item in enumerate(response, 1):
                print(f"   {i}. {item}")
                
    except Exception as e:
        print(f"❌ Error: {e}")


def typed_response_example(ctx: SelectedModelContext) -> None:
    """Request a Pydantic-validated object from the model.

    Args:
        ctx: Selected model context.

    Returns:
        None.
    """
    print("\n" + "="*60)
    print("🔧 TYPED RESPONSE EXAMPLE")
    print("="*60)
    print("Get responses that conform to your data models.\n")
    
    try:
        prompt = "Create a person named Alice, age 30, email alice@example.com"
        print(f"👤 Question: {prompt}")

        if ctx.provider == "openai":
            client = create_client(provider="openai", model=ctx.model)
            person = client.ask_typed(prompt, Person)
        else:
            api_key = os.getenv("LOCAL_OPENAI_API_KEY", "EMPTY")
            client = create_client(
                provider="openai_compatible",
                base_url=ctx.base_url,
                api_key=api_key,
            )
            person = client.ask_typed(prompt, Person, model=ctx.model)
        
        print(f"👤 Person Object:")
        print(f"   Name: {person.name}")
        print(f"   Age: {person.age}")
        print(f"   Email: {person.email}")
        print(f"   Type: {type(person).__name__}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def real_world_examples(ctx: SelectedModelContext) -> None:
    """Run a set of practical prompts (code/data/content).

    Args:
        ctx: Selected model context.

    Returns:
        None.
    """
    print("\n" + "="*60)
    print("🌍 REAL-WORLD EXAMPLES")
    print("="*60)
    print("Practical examples for common use cases.\n")
    
    try:
        # Create client based on provider type
        if ctx.provider == "openai":
            client = create_client(provider="openai", model=ctx.model)
        else:
            api_key = os.getenv("LOCAL_OPENAI_API_KEY", "EMPTY")
            client = create_client(
                provider="openai_compatible",
                base_url=ctx.base_url,
                api_key=api_key,
            )
        
        # Example 1: Code generation
        print("💻 Example 1: Code Generation")
        code_prompt = "Write a Python function to calculate factorial"
        print(f"👤 Question: {code_prompt}")
        code_response = client.ask(code_prompt, model=ctx.model)
        print(f"📝 Generated code:\n{code_response}\n")
        
        # Example 2: Data analysis
        print("📈 Example 2: Data Analysis")
        data_prompt = "Explain what a p-value is in statistics, for beginners"
        print(f"👤 Question: {data_prompt}")
        data_response = client.ask(data_prompt, model=ctx.model)
        print(f"📊 Explanation: {data_response}\n")
        
        # Example 3: Content creation
        print("📝 Example 3: Content Creation")
        content_prompt = "Write a short email announcing a team meeting"
        print(f"👤 Question: {content_prompt}")
        content_response = client.ask(content_prompt, model=ctx.model)
        print(f"📧 Email:\n{content_response}\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def error_handling_examples(ctx: SelectedModelContext) -> None:
    """Demonstrate intentional failures with clear messaging.

    Args:
        ctx: Selected model context.

    Returns:
        None.
    """
    print("\n" + "="*60)
    print("⚠️  ERROR HANDLING EXAMPLES")
    print("="*60)
    print("Learn how to handle errors gracefully.\n")
    
    # Example 1: Invalid JSON request (intentional)
    print("1️⃣  JSON Parsing Error Handling:")
    print("   (This demonstrates intentional error handling)")
    try:
        prompt = "This is not valid JSON"
        if ctx.provider == "openai":
            client = create_client(provider="openai", model=ctx.model)
            response = client.ask_json(prompt)
        else:
            api_key = os.getenv("LOCAL_OPENAI_API_KEY", "EMPTY")
            client = create_client(
                provider="openai_compatible",
                base_url=ctx.base_url,
                api_key=api_key,
            )
            response = client.ask_json(prompt, model=ctx.model)
        
        # This might fail if the model doesn't return valid JSON
        print(f"   🤔 Unexpected success: {response}")
    except JsonParseError as e:
        print(f"   ✅ Caught JSON error: {e}")
        print(f"   💡 Solution: Use ask() instead or prompt for valid JSON")
    except Exception as e:
        print(f"   ✅ Caught other error: {type(e).__name__}")
    
    # Example 2: Network error simulation
    print("\n2️⃣  Network Error Handling:")
    print("   (This demonstrates how to handle connection issues)")
    try:
        # Try to connect to non-existent server to demonstrate error handling
        bad_client = create_client(
            provider="openai_compatible",
            base_url="http://localhost:9999/v1"
        )
        response = bad_client.ask("test", model=ctx.model)
        print(f"   🤔 Unexpected success: {response}")
    except Exception as e:
        print(f"   ✅ Caught network error: {type(e).__name__}")
        print(f"   💡 Solution: Check your network and server status")
    
    # Example 3: Model-specific error
    print("\n3️⃣  Model Configuration Error:")
    print("   (This shows current model is working correctly)")
    try:
        if ctx.provider == "openai":
            client = create_client(provider="openai", model=ctx.model)
            response = client.ask("What is 2+2?")
        else:
            api_key = os.getenv("LOCAL_OPENAI_API_KEY", "EMPTY")
            client = create_client(
                provider="openai_compatible",
                base_url=ctx.base_url,
                api_key=api_key,
            )
            response = client.ask("What is 2+2?", model=ctx.model)

        print(f"   ✅ Current model working: {response.strip()}")
    except Exception as e:
        print(f"   ❌ Model error: {e}")


def provider_comparison_example(ctx: SelectedModelContext, all_models: List[ValidatedModel]) -> None:
    """Compare different AI providers with the same prompt."""
    print("\n" + "="*60)
    print("⚡ PROVIDER COMPARISON")
    print("="*60)
    print("Test the same prompt across different available providers.\n")
    
    import time
    
    prompt = "What is the capital of France? Give a brief answer."
    print(f"👤 Test Question: {prompt}\n")
    
    results = []
    
    # Test all READY models
    for validated_model in all_models:
        if validated_model.status.value != "ready":
            continue
            
        try:
            print(f"🧪 Testing {validated_model.menu_line_text}...")
            
            start_time = time.time()

            # Create client based on provider type
            if validated_model.model_def.provider.value == "openai":
                client = create_client(provider="openai", model=validated_model.model_def.model)
                response = client.ask(prompt)
            else:
                api_key = os.getenv("LOCAL_OPENAI_API_KEY", "EMPTY")
                client = create_client(
                    provider="openai_compatible",
                    base_url=validated_model.model_def.base_url,
                    api_key=api_key,
                )
                response = client.ask(prompt, model=validated_model.model_def.model)
            
            end_time = time.time()
            
            results.append((
                validated_model.menu_line_text,
                response,
                end_time - start_time
            ))
            print(f"   ✅ {response.strip()} ({end_time - start_time:.2f}s)")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Show performance comparison
    if results:
        print(f"\n📊 PERFORMANCE COMPARISON:")
        results.sort(key=lambda x: x[2])  # Sort by response time
        for i, (provider, response, time_taken) in enumerate(results, 1):
            print(f"   {i}. {provider}: {time_taken:.2f}s - {response.strip()}")
    else:
        print("❌ No ready models available for comparison.")
