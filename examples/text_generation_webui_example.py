#!/usr/bin/env python3
"""
Text-Generation-WebUI Usage Example
Demonstrates how to use AI Utilities with text-generation-webui.
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from ai_utilities import create_client

def example_basic_usage():
    """Basic usage example with text-generation-webui."""
    print("🤖 Text-Generation-WebUI Basic Usage")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Create client for text-generation-webui
    client = create_client(
        provider="openai_compatible",
        base_url="http://127.0.0.1:5000/v1",
        api_key=os.getenv("TEXT_GENERATION_WEBUI_API_KEY"),  # Optional
        model="local-model"  # Will be updated to first available model
    )
    
    # Simple chat
    response = client.ask("Hello! Tell me a joke.")
    print(f"🤖 AI: {response}")
    
    # Chat with parameters
    response = client.ask(
        "Write a short poem about AI.",
        max_tokens=100,
        temperature=0.8
    )
    print(f"🎭 Poem: {response}")

def example_streaming():
    """Streaming example with text-generation-webui."""
    print("\n🌊 Text-Generation-WebUI Streaming Example")
    print("=" * 50)
    
    load_dotenv()
    
    client = create_client(
        provider="openai_compatible",
        base_url="http://127.0.0.1:5000/v1",
        api_key=os.getenv("TEXT_GENERATION_WEBUI_API_KEY"),
        model="local-model"
    )
    
    print("🤖 AI (streaming): ", end="", flush=True)
    
    # Stream response
    for chunk in client.stream_ask("Explain quantum computing in simple terms.", max_tokens=150):
        print(chunk, end="", flush=True)
    
    print()  # New line after streaming

def example_multiple_providers():
    """Example using multiple providers including text-generation-webui."""
    print("\n🔄 Multiple Providers Example")
    print("=" * 50)
    
    load_dotenv()
    
    providers = [
        {
            "name": "Text-Generation-WebUI",
            "config": {
                "provider": "openai_compatible",
                "base_url": "http://127.0.0.1:5000/v1",
                "api_key": os.getenv("TEXT_GENERATION_WEBUI_API_KEY"),
                "model": "local-model"
            }
        },
        {
            "name": "Ollama",
            "config": {
                "provider": "openai_compatible",
                "base_url": "http://127.0.0.1:11434/v1",
                "api_key": None,
                "model": "llama3.2:latest"
            }
        }
    ]
    
    question = "What is the meaning of life?"
    
    for provider in providers:
        try:
            print(f"\n🤖 {provider['name']}:")
            client = create_client(**provider['config'])
            response = client.ask(question, max_tokens=50)
            print(f"   {response}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

def example_configuration():
    """Example showing different configuration options."""
    print("\n⚙️ Configuration Examples")
    print("=" * 50)
    
    # Example 1: Local server without API key
    print("1️⃣ Local server (no API key):")
    client1 = create_client(
        provider="openai_compatible",
        base_url="http://127.0.0.1:5000/v1",
        model="local-model"
    )
    
    # Example 2: With API key authentication
    print("2️⃣ With API key authentication:")
    api_key = os.getenv("TEXT_GENERATION_WEBUI_API_KEY")
    if api_key:
        client2 = create_client(
            provider="openai_compatible",
            base_url="http://127.0.0.1:5000/v1",
            api_key=api_key,
            model="local-model"
        )
        print("   ✅ Configured with API key")
    else:
        print("   ⚠️  No API key configured (optional for local)")
    
    # Example 3: Custom settings
    print("3️⃣ Custom settings:")
    client3 = create_client(
        provider="openai_compatible",
        base_url="http://127.0.0.1:5000/v1",
        api_key=os.getenv("TEXT_GENERATION_WEBUI_API_KEY"),
        model="local-model",
        temperature=0.7,
        max_tokens=200,
        timeout=30
    )
    print("   ✅ Configured with custom parameters")

def main():
    """Run all examples."""
    print("🚀 Text-Generation-WebUI Usage Examples")
    print("=" * 60)
    
    try:
        example_basic_usage()
        example_streaming()
        example_multiple_providers()
        example_configuration()
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        print("\n💡 Make sure text-generation-webui is running:")
        print("   python server.py --api --listen")
        print("   # Or with API key:")
        print("   python server.py --api --listen --api-key your-secret-key")

if __name__ == "__main__":
    main()
