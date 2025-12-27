# Add src to path for development usage (works both in repo and when installed)
import sys
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_utilities import create_client, JsonParseError


class Person(BaseModel):
    """Example Pydantic model for typed responses."""
    name: str
    age: int
    email: Optional[str] = None


def main() -> None:
    """
    Example usage of the ai_utilities v1 API with multi-provider switching.
    Demonstrates how the same code works with OpenAI and Ollama interchangeably.
    """
    print("=== AI Utilities v1 Multi-Provider Demo ===\n")
    
    print("🔄 Testing Provider Switching - Same Code, Different AI Backends")
    print("=" * 70)
    
    # Test 1: Try OpenAI first (if API key is available)
    print("\n1. 🌐 Testing OpenAI Provider (Cloud):")
    print("   Setting: AI_PROVIDER=openai")
    
    try:
        # Temporarily set OpenAI provider
        import os
        original_provider = os.getenv('AI_PROVIDER')
        os.environ['AI_PROVIDER'] = 'openai'
        
        client_openai = create_client(model="gpt-3.5-turbo")  # Use cheaper model for demo
        response_openai = client_openai.ask("What is 2+2? Answer with just the number.")
        print(f"   ✅ OpenAI Response: {response_openai.strip()}")
        print(f"   ⏱️  Response time: Fast cloud inference")
        print(f"   💰 Cost: ~$0.002 per request")
        
        # Test JSON mode
        json_openai = client_openai.ask("List 3 colors as JSON array", return_format="json")
        print(f"   ✅ OpenAI JSON: {json_openai}")
        
        # Restore original provider
        if original_provider:
            os.environ['AI_PROVIDER'] = original_provider
        else:
            os.environ.pop('AI_PROVIDER', None)
            
    except Exception as e:
        print(f"   ❌ OpenAI not available: {e}")
        print("   💡 Set AI_API_KEY to test OpenAI")
    
    # Test 2: Test Ollama (local AI)
    print("\n2. 🦙 Testing Ollama Provider (Local):")
    print("   Setting: AI_PROVIDER=openai_compatible, AI_BASE_URL=http://localhost:11434/v1")
    
    try:
        # Configure for Ollama
        import os
        original_provider = os.getenv('AI_PROVIDER')
        original_base_url = os.getenv('AI_BASE_URL')
        original_api_key = os.getenv('AI_API_KEY')
        
        os.environ['AI_PROVIDER'] = 'openai_compatible'
        os.environ['AI_BASE_URL'] = 'http://localhost:11434/v1'
        os.environ['AI_API_KEY'] = 'dummy-key'
        
        client_ollama = create_client(model="llama3.2:latest")
        response_ollama = client_ollama.ask("What is 2+2? Answer with just the number.")
        print(f"   ✅ Ollama Response: {response_ollama.strip()}")
        print(f"   ⏱️  Response time: Local inference (~1s)")
        print(f"   💰 Cost: Free (after hardware)")
        
        # Test JSON mode (works with warning)
        json_ollama = client_ollama.ask("List 3 colors as JSON array", return_format="json")
        print(f"   ✅ Ollama JSON: {json_ollama}")
        
        # Restore original settings
        if original_provider:
            os.environ['AI_PROVIDER'] = original_provider
        else:
            os.environ.pop('AI_PROVIDER', None)
        if original_base_url:
            os.environ['AI_BASE_URL'] = original_base_url
        else:
            os.environ.pop('AI_BASE_URL', None)
        if original_api_key:
            os.environ['AI_API_KEY'] = original_api_key
        else:
            os.environ.pop('AI_API_KEY', None)
            
    except Exception as e:
        print(f"   ❌ Ollama not available: {e}")
        print("   💡 Run 'ollama serve' and 'ollama pull llama3.2:latest' to test Ollama")
    
    # Test 3: Demonstrate the SAME code working with different providers
    print("\n3. 🔄 Demonstrating Code Interchangeability:")
    print("   The SAME function works with BOTH providers!")
    
    def ask_ai_question(question: str, provider_name: str) -> str:
        """Same function, different providers - zero code changes needed!"""
        try:
            if provider_name == "openai":
                client = create_client(model="gpt-3.5-turbo")
            elif provider_name == "ollama":
                # Configure for Ollama
                import os
                os.environ['AI_PROVIDER'] = 'openai_compatible'
                os.environ['AI_BASE_URL'] = 'http://localhost:11434/v1'
                os.environ['AI_API_KEY'] = 'dummy-key'
                client = create_client(model="llama3.2:latest")
            else:
                raise ValueError(f"Unknown provider: {provider_name}")
            
            response = client.ask(question)
            return response.strip()
        except Exception as e:
            return f"Error with {provider_name}: {e}"
    
    # Test the same function with different providers
    question = "What is the capital of France?"
    
    print(f"   Question: {question}")
    openai_result = ask_ai_question(question, "openai")
    print(f"   OpenAI: {openai_result}")
    
    ollama_result = ask_ai_question(question, "ollama")
    print(f"   Ollama: {ollama_result}")
    
    # Test 4: Show provider switching in action
    print("\n4. 🎛️  Provider Switching in Action:")
    print("   Switch between providers with just environment variables:")
    
    print("\n   # Development (free, local):")
    print("   export AI_PROVIDER=openai_compatible")
    print("   export AI_BASE_URL=http://localhost:11434/v1")
    print("   python3 your_app.py  # Uses Ollama")
    
    print("\n   # Production (full features):")
    print("   export AI_PROVIDER=openai")
    print("   export AI_API_KEY=sk-your-key")
    print("   python3 your_app.py  # Uses OpenAI")
    
    print("\n   🎯 SAME CODE, DIFFERENT AI BACKENDS!")
    
    # Continue with the rest of the original demo
    print("\n" + "=" * 70)
    print("📊 Additional Feature Demonstrations:")
    print("=" * 70)
    
    # Use the last working client for remaining demos
    try:
        # Try to use Ollama if available, otherwise fall back to default
        import os
        os.environ['AI_PROVIDER'] = 'openai_compatible'
        os.environ['AI_BASE_URL'] = 'http://localhost:11434/v1'
        os.environ['AI_API_KEY'] = 'dummy-key'
        client = create_client(model="llama3.2:latest")
    except:
        try:
            client = create_client(model="gpt-3.5-turbo")
        except:
            print("❌ No AI provider available for remaining demos")
            return
    
    print("1. Single prompt with progress indicator (default):")
    prompt_single_text = "Who was the first human to walk on the moon?"
    result_single_text = client.ask(prompt_single_text)
    print(f"Question: {prompt_single_text}")
    print(f"Answer: {result_single_text}\n")

    print("2. Multiple prompts with progress indicator:")
    prompts_multiple_text = [
        "Who was the last person to walk on the moon?",
        "What is Kant's categorical imperative in simple terms?",
        "What is the Fibonacci sequence? do not include examples"
    ]

    results_multiple_text = client.ask_many(prompts_multiple_text)

    if results_multiple_text:
        for question, result in zip(prompts_multiple_text, results_multiple_text):
            print(f"Question: {question}")
            print(f"Answer: {result}\n")

    print("3. 🆕 Robust JSON parsing with repair attempts:")
    prompt_robust_json = "List 5 programming languages as JSON array"
    try:
        result_robust_json = client.ask_json(prompt_robust_json, max_repairs=2)
        print(f"Question: {prompt_robust_json}")
        print(f"Answer: {result_robust_json}")
        print(f"Type: {type(result_robust_json)}\n")
    except JsonParseError as e:
        print(f"❌ JSON parsing failed: {e}\n")

    print("4. 🆕 Typed responses with Pydantic validation:")
    prompt_typed = "Create a person named Alice, age 30, email alice@example.com"
    try:
        person = client.ask_typed(prompt_typed, Person, max_repairs=1)
        print(f"Question: {prompt_typed}")
        print(f"Answer: {person}")
        print(f"Name: {person.name}")
        print(f"Age: {person.age}")
        print(f"Email: {person.email}")
        print(f"Type: {type(person)}\n")
    except Exception as e:
        print(f"❌ Typed response failed: {e}\n")

    print("5. 🆕 JSON extraction from text with code fences:")
    prompt_json_fences = "Return JSON data about Python programming language"
    try:
        result_json_fences = client.ask_json(prompt_json_fences)
        print(f"Question: {prompt_json_fences}")
        print(f"Answer: {result_json_fences}")
        print(f"Type: {type(result_json_fences)}\n")
    except JsonParseError as e:
        print(f"❌ JSON parsing failed: {e}\n")

    print("6. Legacy JSON format (still supported):")
    prompt_single = "What are the current top 3 trends in AI, just the title? Please return the answer as a JSON format"
    result_single_json = client.ask_json(prompt_single)
    print(f"Question: {prompt_single}")
    print(f"Answer: {result_single_json}\n")

    print("7. Request without progress indicator:")
    # Create client with progress indicator disabled and real model
    client_no_progress = create_client(model="gpt-4", show_progress=False)
    prompt_custom_model = "What is the capital of France?"
    response = client_no_progress.ask(prompt_custom_model)
    print(f"Question: {prompt_custom_model}")
    print(f"Answer: {response}\n")

    print("8. Custom model with progress indicator:")
    response = client.ask("Explain quantum computing in simple terms")
    print(f"Answer: {response}\n")

    print("=== Demo Complete ===")
    print("\n🎉 New Features Demonstrated:")
    print("✅ Robust JSON parsing with automatic repair attempts")
    print("✅ Typed responses with Pydantic validation")
    print("✅ JSON extraction from text with code fences")
    print("✅ Backward compatibility with existing JSON mode")

if __name__ == "__main__":
    main()
