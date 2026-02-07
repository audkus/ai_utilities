#!/usr/bin/env python3
"""
Step 4: Advanced - Tutorial
Advanced features and patterns for production usage.
"""

import os
import sys
from pathlib import Path
import asyncio
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities import AiClient, AiSettings, AsyncAiClient

def main():
    print("🚀 Step 4: Advanced")
    print("=" * 50)
    
    print("📋 Advanced patterns...")
    
    # Async client
    print("\n  🔄 Async client usage:")
    async def test_async_client():
        client = AsyncAiClient()
        response = await client.ask("What is 42?")
        return response
    
    # Run async test
    print("     Testing async client...")
    start_time = time.time()
    response = asyncio.run(test_async_client())
    end_time = time.time()
    print(f"     Response: {response.text}")
    print(f"     Time: {end_time - start_time:.2f}s")
    
    # Custom settings with multiple providers
    print("\n  ⚙️ Multi-provider configuration:")
    settings = AiSettings(
        provider="auto",  # Auto-select best available
        models={
            "openai": "gpt-4",
            "groq": "llama3-70b-8192"
        },
        fallback="openai"  # Fallback if auto-selection fails
    )
    multi_client = AiClient(settings=settings)
    print(f"  ✅ Multi-client ready: {multi_client.provider}")
    
    # Error handling
    print("\n  🛡️ Error handling:")
    try:
        # This will fail gracefully without API key
        client = AiClient(provider="openai")
        client.ask("This should fail without API key")
    except Exception as e:
        print(f"  ✅ Graceful error handling: {type(e).__name__}")
        print("  💡 Set OPENAI_API_KEY in your environment")
    
    # Usage tracking
    print("\n  📊 Usage tracking:")
    client = AiClient()
    usage = client.get_usage_stats()
    if usage:
        print(f"  ✅ Usage stats: {usage.total_requests} requests")
        print(f"     Total tokens: {usage.total_tokens}")
        print(f"     Total cost: ${usage.total_cost:.4f}")
    else:
        print("  ⚠️ Usage tracking not enabled")
    
    print("\n✅ Advanced features demonstrated!")
    print("  📚 Next: Explore other examples in recipes/ and advanced/")

if __name__ == "__main__":
    main()
