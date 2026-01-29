#!/usr/bin/env python3
"""
Test script for multiple local AI providers.
Compares performance and compatibility across different local servers.
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Load .env for any environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

from ai_utilities import create_client

# Local provider configurations
PROVIDERS = {
    "Ollama": {
        "base_url": "http://localhost:11434/v1",
        "model": "llama3.2:latest",
        "description": "CLI-based, production-ready"
    },
    "LM Studio": {
        "base_url": "http://localhost:1234/v1", 
        "model": "llama-3.2-3b-instruct",
        "description": "GUI-based, user-friendly"
    },
    "Llama.cpp": {
        "base_url": "http://localhost:8080/v1",
        "model": "model",  # Default llama.cpp model name
        "description": "High-performance, CPU/GPU optimized"
    },
    "TextGen WebUI": {
        "base_url": "http://127.0.0.1:7860/v1",
        "model": "local-model",  # Depends on loaded model
        "description": "Feature-rich, extensible"
    }
}

def test_provider(name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Test a single provider and return results."""
    print(f"\n🧪 Testing {name}...")
    print(f"   📡 URL: {config['base_url']}")
    print(f"   🤖 Model: {config['model']}")
    print(f"   📝 {config['description']}")
    
    results = {
        "name": name,
        "available": False,
        "response_time": None,
        "error": None,
        "response": None
    }
    
    try:
        # Create client
        client = create_client(
            provider='openai_compatible',
            base_url=config['base_url']
        )
        
        # Test simple query
        start_time = time.time()
        response = client.ask("What is 2+2? Give a brief answer.", model=config['model'])
        end_time = time.time()
        
        results.update({
            "available": True,
            "response_time": end_time - start_time,
            "response": response.strip()
        })
        
        print(f"   ✅ Available - Response time: {results['response_time']:.2f}s")
        print(f"   💬 Response: {results['response']}")
        
    except Exception as e:
        results["error"] = str(e)
        print(f"   ❌ Not available: {str(e)[:100]}...")
    
    return results

def main():
    """Test all configured providers."""
    print("🔍 Local AI Provider Test Suite")
    print("=" * 50)
    print("Testing multiple local AI providers for compatibility and performance.\n")
    
    results = []
    
    # Test each provider
    for name, config in PROVIDERS.items():
        result = test_provider(name, config)
        results.append(result)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    available_count = sum(1 for r in results if r["available"])
    print(f"✅ Available providers: {available_count}/{len(results)}")
    
    if available_count > 0:
        print("\n🏆 PERFORMANCE RANKING:")
        available_results = [r for r in results if r["available"]]
        available_results.sort(key=lambda x: x["response_time"])
        
        for i, result in enumerate(available_results, 1):
            print(f"   {i}. {result['name']}: {result['response_time']:.2f}s")
    
    print(f"\n❌ Unavailable providers:")
    for result in results:
        if not result["available"]:
            print(f"   • {result['name']}: {result['error'][:50]}...")
    
    print(f"\n🎯 RECOMMENDATIONS:")
    if available_count == 0:
        print("   • No local providers found. Consider installing:")
        print("     - LM Studio (easiest): https://lmstudio.ai/")
        print("     - Ollama (CLI): https://ollama.ai/")
    else:
        print("   • Use the fastest provider for development")
        print("   • Test different models for quality vs speed tradeoffs")
        print("   • Consider hardware requirements for larger models")

if __name__ == "__main__":
    main()
