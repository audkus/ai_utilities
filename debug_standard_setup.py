#!/usr/bin/env python3
"""Minimal debug test for standard setup"""

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, 'src')

from ai_utilities.improved_setup import ImprovedSetupSystem

def debug_standard_setup():
    print('🔍 DEBUG STANDARD SETUP')
    print('=' * 40)
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    try:
        setup = ImprovedSetupSystem()
        
        # Mock inputs for standard setup with mixed case and spaces
        mock_inputs = [
            '2',  # Choose Standard Setup
            '1',  # Choose OpenAI provider
            'gpt-3.5-turbo',  # Model
            '0.8',  # Temperature
            '2000',  # Max tokens
            '45',  # Timeout
            '',  # Base URL (default)
            '7',  # Update check days (weekly)
            ' TRUE ',  # Enable caching - mixed case with spaces!
            'sqlite',  # Cache backend
            '1800',  # Cache TTL
            'per_process'  # Usage scope
        ]
        
        print('Running interactive_tiered_setup with mocked inputs...')
        
        with patch('builtins.input', side_effect=mock_inputs):
            # with patch('builtins.print'):  # Removed print suppression to debug
            with patch.object(setup, '_configure_multi_provider_env_vars') as mock_env:
                mock_env.return_value = {'OPENAI_API_KEY': 'test-key'}
                
                result = setup.interactive_tiered_setup()
                
                print(f'✅ Setup completed successfully')
                print(f'   Setup level: {result.get("setup_level", "NOT FOUND")}')
                print(f'   Config keys: {list(result.get("config", {}).keys())}')
                
                config = result.get('config', {})
                print(f'   cache_enabled: {config.get("cache_enabled", "NOT FOUND")}')
                print(f'   cache_backend: {config.get("cache_backend", "NOT FOUND")}')
                
                # Check .env file
                env_file = Path('.') / '.env'
                if env_file.exists():
                    content = env_file.read_text()
                    print(f'   .env file exists ({len(content)} chars)')
                    
                    if 'AI_CACHE_ENABLED=True' in content or 'AI_CACHE_ENABLED=true' in content:
                        print('   ✅ AI_CACHE_ENABLED found in .env')
                    else:
                        print('   ❌ AI_CACHE_ENABLED NOT found in .env')
                        print('   Cache-related lines in .env:')
                        for line in content.split('\n'):
                            if 'CACHE' in line:
                                print(f'      {line}')
                else:
                    print('   ❌ .env file not found')
                        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        os.chdir(original_cwd)

if __name__ == '__main__':
    debug_standard_setup()
