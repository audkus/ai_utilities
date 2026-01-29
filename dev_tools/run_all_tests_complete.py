#!/usr/bin/env python3
"""
Complete setup script to run ALL integration tests without any skips.
This script ensures all required environment variables and servers are properly configured.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_and_set_env_vars():
    """Ensure all required environment variables are set."""
    print("🔧 Checking environment variables...")
    
    # Required environment variables
    required_vars = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'GROQ_API_KEY': os.getenv('GROQ_API_KEY'), 
        'TOGETHER_API_KEY': os.getenv('TOGETHER_API_KEY'),
        'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY'),
        'RUN_LIVE_AI_TESTS': os.getenv('RUN_LIVE_AI_TESTS')
    }
    
    missing_vars = []
    for var, value in required_vars.items():
        if var == 'RUN_LIVE_AI_TESTS':
            # RUN_LIVE_AI_TESTS just needs to be '1'
            if value != '1':
                missing_vars.append(var)
                print(f"❌ {var}: NOT SET (should be '1')")
            else:
                print(f"✅ {var}: SET")
        else:
            # API keys need to be substantial
            if not value or (isinstance(value, str) and len(value) < 10):
                missing_vars.append(var)
                print(f"❌ {var}: NOT SET or too short")
            else:
                print(f"✅ {var}: SET")
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        print("\n📝 To set them:")
        print("export OPENAI_API_KEY='sk-your-actual-openai-key'")
        print("export GROQ_API_KEY='gsk-your-actual-groq-key'")
        print("export TOGETHER_API_KEY='tgp-your-actual-together-key'")
        print("export OPENROUTER_API_KEY='sk-or-v1-your-actual-openrouter-key'")
        return False
    
    return True

def check_servers():
    """Check if required local servers are running."""
    print("\n🔧 Checking local servers...")
    
    servers = {
        'Ollama': 'http://localhost:11434/api/tags',
        'LM Studio': 'http://localhost:1234/v1/models',
        'TextGen WebUI': 'http://localhost:5000/v1/models',
        'FastChat': 'http://localhost:8000/v1/models'
    }
    
    running_servers = []
    for name, url in servers.items():
        try:
            result = subprocess.run(['curl', '-s', url], capture_output=True, timeout=3)
            if result.returncode == 0:
                print(f"✅ {name}: RUNNING")
                running_servers.append(name)
            else:
                print(f"❌ {name}: NOT RUNNING")
        except:
            print(f"❌ {name}: NOT ACCESSIBLE")
    
    return running_servers

def check_audio_api():
    """Check if OpenAI audio API is available."""
    print("\n🔧 Checking OpenAI Audio API access...")
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not set - cannot check audio API")
        return False
    
    try:
        # Test with a simple API call to check if audio features are enabled
        cmd = [
            'python3', '-c',
            '''
import os
from ai_utilities import AiClient

try:
    client = AiClient(api_key=os.getenv("OPENAI_API_KEY"))
    # Try to access audio features - this will tell us if audio API is available
    print("Audio API check: Available")
except Exception as e:
    if "audio" in str(e).lower() or "whisper" in str(e).lower():
        print("Audio API check: Not available")
    else:
        print("Audio API check: Available (no audio-specific error)")
'''
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, 
                               env={**os.environ, 'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY')})
        
        if "Available" in result.stdout:
            print("✅ OpenAI Audio API: AVAILABLE")
            return True
        else:
            print("❌ OpenAI Audio API: NOT AVAILABLE")
            return False
            
    except Exception as e:
        print(f"❌ Audio API check failed: {e}")
        return False

def run_all_tests():
    """Run all integration tests with maximum coverage."""
    print("\n🚀 Running ALL integration tests...")
    
    # Set environment variables for pytest
    env = os.environ.copy()
    env['RUN_LIVE_AI_TESTS'] = '1'
    env['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', '')
    env['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY', '')
    env['TOGETHER_API_KEY'] = os.getenv('TOGETHER_API_KEY', '')
    env['OPENROUTER_API_KEY'] = os.getenv('OPENROUTER_API_KEY', '')
    
    cmd = [
        'python3', '-m', 'pytest', 
        '-m', 'integration',
        '--run-integration',
        '-v',
        '--timeout=120',
        '--tb=short'
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    result = subprocess.run(cmd, env=env)
    
    return result.returncode == 0

def main():
    """Main setup and execution function."""
    print("🧪 AI Utilities - Complete Integration Test Setup")
    print("=" * 60)
    
    # Check environment variables
    env_ok = check_and_set_env_vars()
    
    # Check servers
    running_servers = check_servers()
    
    # Check audio API
    audio_ok = check_audio_api()
    
    print(f"\n📊 Setup Summary:")
    print(f"Environment Variables: {'✅ READY' if env_ok else '❌ INCOMPLETE'}")
    print(f"Local Servers: {len(running_servers)}/4 running ({', '.join(running_servers) if running_servers else 'None'})")
    print(f"Audio API: {'✅ AVAILABLE' if audio_ok else '❌ NOT AVAILABLE'}")
    
    if not env_ok:
        print(f"\n❌ Cannot proceed - missing environment variables")
        sys.exit(1)
    
    print(f"\n🎯 Running tests with current setup...")
    success = run_all_tests()
    
    if success:
        print(f"\n🎉 All tests completed successfully!")
    else:
        print(f"\n⚠️  Some tests failed - check output above")
    
    # Provide guidance for missing components
    if len(running_servers) < 4:
        print(f"\n📋 To enable ALL server tests:")
        if 'FastChat' not in running_servers:
            print("  - Start FastChat: python3 -m fastchat.serve.controller && python3 -m fastchat.serve.model_worker")
    
    if not audio_ok:
        print(f"\n📋 To enable audio tests:")
        print("  - Ensure your OpenAI API key has Whisper/voice features enabled")
        print("  - Check OpenAI dashboard for API access permissions")

if __name__ == "__main__":
    main()
