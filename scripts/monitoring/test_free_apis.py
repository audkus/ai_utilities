#!/usr/bin/env python3
"""
Test script for free online AI APIs.
Tests various free cloud providers for compatibility and performance.
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Load .env for API keys
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

from ai_utilities import create_client

# Free API configurations
FREE_APIS = {
    "Hugging Face (Free)": {
        "base_url": "https://router.huggingface.co/api",
        "api_key": None,  # No API key needed
        "model": "microsoft/DialoGPT-medium",
        "description": "Completely free, no registration required"
    },
    "Groq (Free Tier)": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": "GROQ_API_KEY",  # Set in .env
        "model": "llama3-8b-8192",
        "description": "Fastest inference, 8,000 requests/day free"
    },
    "Together AI (Free Credits)": {
        "base_url": "https://api.together.xyz/v1",
        "api_key": "TOGETHER_API_KEY",  # Set in .env
        "model": "meta-llama/Llama-3.2-3B-Instruct-Turbo",
        "description": "$5 free credits, 100+ models"
    },
    "OpenRouter (Free Credits)": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": "OPENROUTER_API_KEY",  # Set in .env
        "model": "meta-llama/llama-3.2-3b-instruct:free",
        "description": "$5 free credits, access to all models"
    }
}

def get_api_key(key_name: str) -> Optional[str]:
    """Get API key from environment variables."""
    import os
    return os.getenv(key_name)

def test_api(name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Test a single API and return results."""
    print(f"\n🌐 Testing {name}...")
    print(f"   📡 URL: {config['base_url']}")
    print(f"   🤖 Model: {config['model']}")
    print(f"   📝 {config['description']}")
    
    results = {
        "name": name,
        "available": False,
        "response_time": None,
        "error": None,
        "response": None,
        "requires_key": config['api_key'] is not None
    }
    
    try:
        # Get API key if needed
        api_key = None
        if config['api_key']:
            api_key = get_api_key(config['api_key'])
            if not api_key:
                results["error"] = f"API key {config['api_key']} not found in environment"
                print(f"   ⚠️  {results['error']}")
                return results
            print(f"   🔑 Using API key: {config['api_key']}")
        else:
            print(f"   🆓 No API key required")
        
        # Create client
        client = create_client(
            provider='openai_compatible',
            base_url=config['base_url'],
            api_key=api_key or "dummy-key"  # Some APIs require a key even if not used
        )
        
        # Test simple query
        test_prompt = "What is 2+2? Give a very brief answer."
        start_time = time.time()
        response = client.ask(test_prompt, model=config['model'])
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
        print(f"   ❌ Error: {str(e)[:100]}...")
    
    return results

def show_setup_instructions():
    """Show setup instructions for APIs that require keys."""
    print("\n🔧 SETUP INSTRUCTIONS:")
    print("=" * 50)
    
    instructions = {
        "Groq": {
            "url": "https://console.groq.com/",
            "env_var": "GROQ_API_KEY",
            "steps": [
                "1. Go to https://console.groq.com/",
                "2. Sign up for free account",
                "3. Go to API Keys section",
                "4. Create new API key",
                "5. Add to .env: GROQ_API_KEY=your-key-here"
            ]
        },
        "Together AI": {
            "url": "https://api.together.xyz/",
            "env_var": "TOGETHER_API_KEY", 
            "steps": [
                "1. Go to https://api.together.xyz/",
                "2. Sign up for free account",
                "3. Get $5 free credits",
                "4. Go to API Keys section",
                "5. Add to .env: TOGETHER_API_KEY=your-key-here"
            ]
        },
        "OpenRouter": {
            "url": "https://openrouter.ai/",
            "env_var": "OPENROUTER_API_KEY",
            "steps": [
                "1. Go to https://openrouter.ai/",
                "2. Sign up for free account", 
                "3. Get $5 free credits",
                "4. Go to API Keys section",
                "5. Add to .env: OPENROUTER_API_KEY=your-key-here"
            ]
        }
    }
    
    for service, info in instructions.items():
        print(f"\n🚀 {service}:")
        for step in info["steps"]:
            print(f"   {step}")

def main():
    """Test all free APIs."""
    print("🌐 Free Online AI API Test Suite")
    print("=" * 50)
    print("Testing various free cloud AI providers.\n")
    
    results = []
    
    # Test each API
    for name, config in FREE_APIS.items():
        result = test_api(name, config)
        results.append(result)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    available_count = sum(1 for r in results if r["available"])
    print(f"✅ Working APIs: {available_count}/{len(results)}")
    
    if available_count > 0:
        print("\n🏆 PERFORMANCE RANKING:")
        available_results = [r for r in results if r["available"]]
        available_results.sort(key=lambda x: x["response_time"])
        
        for i, result in enumerate(available_results, 1):
            key_status = "🔑" if result["requires_key"] else "🆓"
            print(f"   {i}. {result['name']} {key_status}: {result['response_time']:.2f}s")
    
    print(f"\n❌ Not working:")
    for result in results:
        if not result["available"]:
            key_status = "🔑" if result["requires_key"] else "🆓"
            print(f"   {key_status} {result['name']}: {result['error'][:50]}...")
    
    # Show setup instructions for those requiring keys
    needs_setup = [r for r in results if not r["available"] and r["requires_key"]]
    if needs_setup:
        show_setup_instructions()
    
    print(f"\n🎯 RECOMMENDATIONS:")
    if available_count > 0:
        print("   • Use Hugging Face for quick testing (no setup required)")
        print("   • Use Groq for fastest inference")
        print("   • Use Together/OpenRouter for model variety")
    else:
        print("   • Try Hugging Face first (no API key needed)")
        print("   • Set up API keys for other services")

if __name__ == "__main__":
    main()
