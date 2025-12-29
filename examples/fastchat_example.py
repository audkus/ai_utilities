#!/usr/bin/env python3
"""
FastChat Usage Example
Demonstrates how to use AI Utilities with FastChat.
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from ai_utilities import create_client

def example_basic_usage():
    """Basic usage example with FastChat."""
    print("🤖 FastChat Basic Usage")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    # Create client for FastChat
    client = create_client(
        provider="openai_compatible",
        base_url="http://127.0.0.1:8000/v1",
        api_key=os.getenv("FASTCHAT_API_KEY"),  # Optional
        model="vicuna-7b-v1.5"
    )
    
    # Simple chat
    response = client.ask("Hello! Tell me about FastChat.")
    print(f"🤖 AI: {response}")
    
    # Chat with parameters
    response = client.ask(
        "Explain the benefits of open-source AI models.",
        max_tokens=150,
        temperature=0.8
    )
    print(f"🎭 Explanation: {response}")

def example_streaming():
    """Streaming example with FastChat."""
    print("\n🌊 FastChat Streaming Example")
    print("=" * 40)
    
    load_dotenv()
    
    client = create_client(
        provider="openai_compatible",
        base_url="http://127.0.0.1:8000/v1",
        api_key=os.getenv("FASTCHAT_API_KEY"),
        model="vicuna-7b-v1.5"
    )
    
    print("🤖 AI (streaming): ", end="", flush=True)
    
    # Stream response
    for chunk in client.stream_ask("Describe the FastChat project in detail.", max_tokens=200):
        print(chunk, end="", flush=True)
    
    print()  # New line after streaming

def example_multiple_models():
    """Example using multiple FastChat models."""
    print("\n🔄 Multiple FastChat Models Example")
    print("=" * 45)
    
    load_dotenv()
    
    # Different FastChat models you might have loaded
    models = [
        {
            "name": "Vicuna-7B",
            "config": {
                "provider": "openai_compatible",
                "base_url": "http://127.0.0.1:8000/v1",
                "api_key": os.getenv("FASTCHAT_API_KEY"),
                "model": "vicuna-7b-v1.5"
            }
        },
        {
            "name": "Vicuna-13B", 
            "config": {
                "provider": "openai_compatible",
                "base_url": "http://127.0.0.1:8000/v1",
                "api_key": os.getenv("FASTCHAT_API_KEY"),
                "model": "vicuna-13b-v1.5"
            }
        }
    ]
    
    question = "What is the difference between 7B and 13B parameter models?"
    
    for model in models:
        try:
            print(f"\n🤖 {model['name']}:")
            client = create_client(**model['config'])
            response = client.ask(question, max_tokens=100)
            print(f"   {response}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

def example_configuration():
    """Example showing different configuration options."""
    print("\n⚙️ FastChat Configuration Examples")
    print("=" * 45)
    
    # Example 1: Local server without API key
    print("1️⃣ Local server (no API key):")
    client1 = create_client(
        provider="openai_compatible",
        base_url="http://127.0.0.1:8000/v1",
        model="vicuna-7b-v1.5"
    )
    
    # Example 2: With API key authentication
    print("2️⃣ With API key authentication:")
    api_key = os.getenv("FASTCHAT_API_KEY")
    if api_key:
        client2 = create_client(
            provider="openai_compatible",
            base_url="http://127.0.0.1:8000/v1",
            api_key=api_key,
            model="vicuna-7b-v1.5"
        )
        print("   ✅ Configured with API key")
    else:
        print("   ⚠️  No API key configured (optional for local)")
    
    # Example 3: Custom settings
    print("3️⃣ Custom settings:")
    client3 = create_client(
        provider="openai_compatible",
        base_url="http://127.0.0.1:8000/v1",
        api_key=os.getenv("FASTCHAT_API_KEY"),
        model="vicuna-7b-v1.5",
        temperature=0.7,
        max_tokens=300,
        timeout=60
    )
    print("   ✅ Configured with custom parameters")

def example_fastchat_workflow():
    """Example showing typical FastChat workflow."""
    print("\n🔧 FastChat Workflow Example")
    print("=" * 40)
    
    print("FastChat requires three components:")
    print("1. Controller (manages workers)")
    print("2. Model Worker (loads and serves models)")
    print("3. OpenAI API Server (provides the API)")
    print("")
    print("Starting commands:")
    print("# Terminal 1 - Start controller")
    print("python3 -m fastchat.serve.controller")
    print("")
    print("# Terminal 2 - Start model worker")
    print("python3 -m fastchat.serve.model_worker --model-path lmsys/vicuna-7b-v1.5")
    print("")
    print("# Terminal 3 - Start API server")
    print("python3 -m fastchat.serve.openai_api_server --host localhost --port 8000")
    print("")
    print("Then use AI Utilities to connect:")
    
    try:
        load_dotenv()
        client = create_client(
            provider="openai_compatible",
            base_url="http://127.0.0.1:8000/v1",
            model="vicuna-7b-v1.5"
        )
        
        response = client.ask("Hello! I'm connected through FastChat.", max_tokens=50)
        print(f"✅ Connected! Response: {response}")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("Make sure FastChat is running with all three components.")

def main():
    """Run all examples."""
    print("🚀 FastChat Usage Examples")
    print("=" * 50)
    
    try:
        example_basic_usage()
        example_streaming()
        example_multiple_models()
        example_configuration()
        example_fastchat_workflow()
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        print("\n💡 Make sure FastChat is running:")
        print("   1. python3 -m fastchat.serve.controller")
        print("   2. python3 -m fastchat.serve.model_worker --model-path lmsys/vicuna-7b-v1.5")
        print("   3. python3 -m fastchat.serve.openai_api_server --host localhost --port 8000")

if __name__ == "__main__":
    main()
