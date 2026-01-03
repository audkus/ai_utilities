"""
🔍 Model Validation Example

Shows how to test if your AI setup is working correctly.
This replaces the complex demo system with a simple validation approach.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities import AiClient, AiSettings
from ai_utilities.providers import MissingOptionalDependencyError


def test_basic_setup():
    """Test if basic AI setup is working."""
    print("🔍 Testing Basic AI Setup")
    print("=" * 40)
    
    try:
        # Test 1: Can we import everything?
        print("✅ Import test passed")
        
        # Test 2: Can we create settings?
        settings = AiSettings(provider="openai", model="gpt-3.5-turbo")
        print("✅ Settings creation passed")
        
        # Test 3: Can we create client?
        client = AiClient(settings=settings)
        print("✅ Client creation passed")
        
        # Test 4: Can we make a simple request?
        print("\n📡 Testing API connection...")
        try:
            result = client.ask("Say 'test'", cache_namespace="validation")
            # Handle different response types
            response_text = result.text if hasattr(result, 'text') else str(result)
            if "test" in response_text.lower():
                print("✅ API connection test passed")
                return True
            else:
                print("⚠️  API responded but unexpected content")
                print(f"   Got: {response_text[:100]}...")
                return False
        except Exception as e:
            if "api key" in str(e).lower():
                print("❌ API key missing or invalid")
                print("💡 Set OPENAI_API_KEY environment variable")
                return False
            else:
                print(f"❌ API test failed: {e}")
                return False
                
    except MissingOptionalDependencyError as e:
        print(f"❌ Missing dependencies: {e}")
        print("💡 Run: pip install ai-utilities[openai]")
        return False
    except Exception as e:
        print(f"❌ Setup test failed: {e}")
        return False


def test_different_providers():
    """Test different provider configurations."""
    print("\n🔄 Testing Different Providers")
    print("=" * 40)
    
    providers = [
        {"provider": "openai", "model": "gpt-3.5-turbo"},
        {"provider": "openai", "model": "gpt-4"},
    ]
    
    for i, config in enumerate(providers, 1):
        print(f"\n{i}. Testing {config['provider']} with {config['model']}:")
        try:
            settings = AiSettings(**config)
            client = AiClient(settings=settings)
            result = client.ask("Brief test", cache_namespace="validation")
            print(f"   ✅ {config['model']} works")
        except Exception as e:
            print(f"   ❌ {config['model']} failed: {e}")


def test_error_handling():
    """Test error handling with invalid configurations."""
    print("\n🚨 Testing Error Handling")
    print("=" * 40)
    
    # Test 1: Invalid provider
    print("1. Testing invalid provider...")
    try:
        settings = AiSettings(provider="invalid_provider")
        client = AiClient(settings=settings)
        client.ask("test")
        print("   ❌ Should have failed!")
    except Exception as e:
        print(f"   ✅ Correctly caught error: {type(e).__name__}")
    
    # Test 2: Missing API key
    print("\n2. Testing missing API key...")
    try:
        # Temporarily clear API key
        import os
        original_key = os.environ.get("OPENAI_API_KEY")
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        
        settings = AiSettings(provider="openai")
        client = AiClient(settings=settings)
        client.ask("test")
        print("   ❌ Should have failed!")
    except Exception as e:
        print(f"   ✅ Correctly caught error: {type(e).__name__}")
    finally:
        # Restore API key
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key


def main():
    """Run all validation tests."""
    print("🧪 AI Utilities Validation Suite")
    print("=" * 50)
    print("This will test your AI setup and help diagnose issues.\n")
    
    # Run tests
    basic_ok = test_basic_setup()
    
    if basic_ok:
        test_different_providers()
        test_error_handling()
        
        print("\n🎉 Validation Complete!")
        print("Your AI Utilities setup is working correctly.")
    else:
        print("\n❌ Validation Failed!")
        print("Please fix the issues above before using AI Utilities.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
