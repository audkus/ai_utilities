#!/usr/bin/env python3
"""
🧪 Multi-Provider AI Testing Script

This script tests the ai_utilities library across multiple AI providers:
- OpenAI (cloud)
- Ollama (local)
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from ai_utilities import create_client
from typing import Any, List, Dict

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_utilities import AiClient, AiSettings, ProviderConfigurationError


def test_provider(name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Test a specific provider configuration."""
    print(f"\n{'='*60}")
    print(f"🧪 Testing {name}")
    print(f"{'='*60}")
    
    try:
        # Create settings and client
        settings = AiSettings(**config)
        client = AiClient(settings)
        
        results = {
            'provider': name,
            'config': config,
            'success': False,
            'error': None,
            'response_time': None,
            'response': None,
            'json_response': None,
            'capabilities': []
        }
        
        # Test 1: Basic text response
        print("1. Testing basic text response...")
        start_time = time.time()
        response = client.ask("What is 2+2? Answer with just the number.")
        response_time = time.time() - start_time
        
        results['response_time'] = response_time
        results['response'] = response.strip()
        results['capabilities'].append('text')
        
        print(f"   ✅ Response: {response.strip()}")
        print(f"   ⏱️  Time: {response_time:.2f}s")
        
        # Test 2: JSON mode (if supported)
        print("2. Testing JSON mode...")
        try:
            json_response = client.ask(
                'List 3 colors as a JSON array: ["red", "blue", "green"]',
                return_format='json'
            )
            results['json_response'] = json_response
            results['capabilities'].append('json')
            print(f"   ✅ JSON: {json_response}")
        except Exception as e:
            print(f"   ⚠️  JSON mode issue: {e}")
        
        # Test 3: Multiple requests
        print("3. Testing multiple requests...")
        try:
            prompts = ["What is 1+1?", "What is 2+2?", "What is 3+3?"]
            start_time = time.time()
            responses = client.ask_many(prompts)
            multi_time = time.time() - start_time
            print(f"   ✅ {len(responses)} responses in {multi_time:.2f}s")
            results['capabilities'].append('batch')
        except Exception as e:
            print(f"   ⚠️  Batch issue: {e}")
        
        results['success'] = True
        print(f"🎉 {name} test completed successfully!")
        
    except ProviderConfigurationError as e:
        results['error'] = str(e)
        print(f"❌ Configuration error: {e}")
    except Exception as e:
        results['error'] = str(e)
        print(f"❌ Test failed: {e}")
    
    return results


def get_provider_configs() -> Dict[str, Dict[str, Any]]:
    """Get configurations for all available providers."""
    configs = {
        # Local Providers
        'ollama': {
            'provider': 'openai_compatible',
            'base_url': 'http://localhost:11434/v1',
            'api_key': 'dummy-key',
            'model': 'llama3.2:latest',
            'timeout': 30
        },
        'vllm': {
            'provider': 'openai_compatible',
            'base_url': 'http://localhost:8000/v1',
            'api_key': 'dummy-key',
            'model': 'meta-llama/Llama-2-7b-chat-hf',
            'timeout': 30
        },
        'lm_studio': {
            'provider': 'openai_compatible',
            'base_url': 'http://localhost:1234/v1',
            'api_key': 'dummy-key',
            'model': 'local-model',
            'timeout': 30
        },
        'oobabooga': {
            'provider': 'openai_compatible',
            'base_url': 'http://localhost:7860/v1',
            'api_key': 'dummy-key',
            'model': 'local-model',
            'timeout': 30
        },
        'localai': {
            'provider': 'openai_compatible',
            'base_url': 'http://localhost:8080/v1',
            'api_key': 'dummy-key',
            'model': 'local-model',
            'timeout': 30
        },
        
        # Cloud Providers
        'openai': {
            'provider': 'openai',
            'api_key': os.getenv('OPENAI_API_KEY'),
            'model': 'gpt-3.5-turbo',
            'timeout': 30
        },
        'together_ai': {
            'provider': 'openai_compatible',
            'base_url': 'https://api.together.xyz/v1',
            'api_key': os.getenv('TOGETHER_API_KEY'),
            'model': 'meta-llama/Llama-2-7b-chat-hf',
            'timeout': 30
        },
        'groq': {
            'provider': 'openai_compatible',
            'base_url': 'https://api.groq.com/openai/v1',
            'api_key': os.getenv('GROQ_API_KEY'),
            'model': 'mixtral-8x7b-32768',
            'timeout': 30
        },
        'anyscale': {
            'provider': 'openai_compatible',
            'base_url': 'https://api.endpoints.anyscale.com/v1',
            'api_key': os.getenv('ANYSCALE_API_KEY'),
            'model': 'meta-llama/Llama-2-7b-chat-hf',
            'timeout': 30
        },
        'fireworks': {
            'provider': 'openai_compatible',
            'base_url': 'https://api.fireworks.ai/inference/v1',
            'api_key': os.getenv('FIREWORKS_API_KEY'),
            'model': 'accounts/fireworks/models/llama-v2-7b-chat',
            'timeout': 30
        },
        'replicate': {
            'provider': 'openai_compatible',
            'base_url': 'https://api.replicate.com/v1',
            'api_key': os.getenv('REPLICATE_API_KEY'),
            'model': 'replicate/llama-2-70b-chat',
            'timeout': 30
        },
        
        # Enterprise Providers
        'azure_openai': {
            'provider': 'openai_compatible',
            'base_url': os.getenv('AZURE_OPENAI_ENDPOINT', 'https://your-resource.openai.azure.com/'),
            'api_key': os.getenv('AZURE_OPENAI_KEY'),
            'model': os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4'),
            'timeout': 30
        },
        'vertex_ai': {
            'provider': 'openai_compatible',
            'base_url': 'https://us-central1-aiplatform.googleapis.com/v1/projects/your-project/locations/us-central1/publishers/google/models',
            'api_key': os.getenv('GOOGLE_API_KEY'),
            'model': 'chat-bison',
            'timeout': 30
        },
        'bedrock': {
            'provider': 'openai_compatible',
            'base_url': 'https://bedrock-runtime.us-east-1.amazonaws.com',
            'api_key': os.getenv('AWS_ACCESS_KEY_ID'),  # Simplified for demo
            'model': 'anthropic.claude-v2',
            'timeout': 30
        }
    }
    return configs


def check_provider_availability(name: str, config: Dict[str, Any]) -> bool:
    """Check if a provider is likely available."""
    # Local providers - check if server is running
    if name == 'ollama':
        try:
            import requests
            response = requests.get('http://localhost:11434/api/tags', timeout=2)
            return response.status_code == 200
        except:
            return False
    
    elif name == 'vllm':
        try:
            import requests
            response = requests.get('http://localhost:8000/v1/models', timeout=2)
            return response.status_code == 200
        except:
            return False
    
    elif name == 'lm_studio':
        try:
            import requests
            response = requests.get('http://localhost:1234/v1/models', timeout=2)
            return response.status_code == 200
        except:
            return False
    
    elif name == 'oobabooga':
        try:
            import requests
            response = requests.get('http://localhost:7860/v1/models', timeout=2)
            return response.status_code == 200
        except:
            return False
    
    elif name == 'localai':
        try:
            import requests
            response = requests.get('http://localhost:8080/v1/models', timeout=2)
            return response.status_code == 200
        except:
            return False
    
    # Cloud providers - check if API key is present
    elif name == 'openai':
        return bool(config.get('api_key'))
    
    elif name == 'together_ai':
        return bool(config.get('api_key'))
    
    elif name == 'groq':
        return bool(config.get('api_key'))
    
    elif name == 'anyscale':
        return bool(config.get('api_key'))
    
    elif name == 'fireworks':
        return bool(config.get('api_key'))
    
    elif name == 'replicate':
        return bool(config.get('api_key'))
    
    # Enterprise providers - check if credentials are present
    elif name == 'azure_openai':
        return bool(config.get('api_key'))
    
    elif name == 'vertex_ai':
        return bool(config.get('api_key'))
    
    elif name == 'bedrock':
        return bool(config.get('api_key'))
    
    return True


def print_summary(results: List[Dict[str, Any]]):
    """Print a summary of all test results."""
    print(f"\n{'='*80}")
    print("📊 TEST SUMMARY")
    print(f"{'='*80}")
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    
    if successful:
        print(f"\n🎉 Successful Providers:")
        for result in successful:
            time_str = f"{result['response_time']:.2f}s" if result['response_time'] else "N/A"
            caps = ", ".join(result['capabilities'])
            print(f"   • {result['provider']}: {time_str} | Capabilities: {caps}")
    
    if failed:
        print(f"\n❌ Failed Providers:")
        for result in failed:
            print(f"   • {result['provider']}: {result['error']}")
    
    # Performance comparison
    if len(successful) > 1:
        print(f"\n⚡ Performance Comparison:")
        sorted_results = sorted(successful, key=lambda x: x['response_time'] or float('inf'))
        for i, result in enumerate(sorted_results, 1):
            if result['response_time']:
                print(f"   {i}. {result['provider']}: {result['response_time']:.2f}s")
    
    print(f"\n🏆 Multi-Provider AI Library Test Complete!")


def main():
    parser = argparse.ArgumentParser(description="Test multi-provider AI functionality")
    parser.add_argument(
        '--providers', 
        nargs='+', 
        choices=[
            'ollama', 'vllm', 'lm_studio', 'oobabooga', 'localai',  # Local
            'openai', 'together_ai', 'groq', 'anyscale', 'fireworks', 'replicate',  # Cloud
            'azure_openai', 'vertex_ai', 'bedrock'  # Enterprise
        ],
        default=['ollama'],
        help='Providers to test (default: ollama)'
    )
    parser.add_argument(
        '--skip-unavailable',
        action='store_true',
        help='Skip providers that appear to be unavailable'
    )
    
    args = parser.parse_args()
    
    print("🧪 Multi-Provider AI Testing Script")
    print("=" * 80)
    print("Testing ai_utilities library across multiple AI providers")
    
    # Get configurations
    all_configs = get_provider_configs()
    test_configs = {name: all_configs[name] for name in args.providers}
    
    print(f"\n📋 Providers to test: {', '.join(args.providers)}")
    
    # Check availability if requested
    if args.skip_unavailable:
        print("\n🔍 Checking provider availability...")
        available = []
        for name, config in test_configs.items():
            if check_provider_availability(name, config):
                available.append(name)
                print(f"   ✅ {name}: Available")
            else:
                print(f"   ❌ {name}: Not available - skipping")
        
        test_configs = {name: test_configs[name] for name in available}
        
        if not test_configs:
            print("\n❌ No providers available for testing!")
            return
    
    # Run tests
    results = []
    for name, config in test_configs.items():
        result = test_provider(name, config)
        results.append(result)
    
    # Print summary
    print_summary(results)


if __name__ == "__main__":
    main()
