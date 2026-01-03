"""
Centralized API key resolution for ai_utilities.

This module provides reliable API key handling across terminal sessions and IDE environments
with proper precedence and helpful error messages.
"""

import os
import sys
from typing import Optional
from pathlib import Path


class MissingApiKeyError(RuntimeError):
    """Raised when API key is required but not found in any location."""
    
    def __init__(self) -> None:
        message = self._get_platform_specific_message()
        super().__init__(message)
    
    def _get_platform_specific_message(self) -> str:
        """Generate OS-specific setup instructions."""
        
        # Platform detection
        is_windows = sys.platform == "win32"
        
        # Build platform-specific instructions
        if is_windows:
            env_commands = """# Windows PowerShell (recommended):
$env:AI_API_KEY="your-openai-api-key-here"

# Windows Command Prompt (cmd.exe):
set AI_API_KEY=your-openai-api-key-here"""
            
            permanent_commands = """# Permanent setup (Windows PowerShell - run as Administrator):
setx AI_API_KEY "your-openai-api-key-here"

# Or add to your PowerShell profile:
echo '$env:AI_API_KEY="your-openai-api-key-here"' >> $PROFILE"""
            
        else:  # macOS or Linux
            env_commands = """# macOS/Linux (zsh/bash):
export AI_API_KEY="your-openai-api-key-here"

# Windows PowerShell (for cross-platform reference):
$env:AI_API_KEY="your-openai-api-key-here" """
            
            permanent_commands = """# Permanent setup (add to shell profile):
echo 'export AI_API_KEY="your-openai-api-key-here"' >> ~/.zshrc  # macOS default
# or: echo 'export AI_API_KEY="your-openai-api-key-here"' >> ~/.bashrc  # Linux default
source ~/.zshrc  # or source ~/.bashrc"""
        
        # Build the complete message
        message = f"""
KEY REQUIRED: AI_API_KEY

The AI utilities library requires an OpenAI API key to function.
The 'AI_API_KEY' environment variable was not found in any location.

QUICK SETUP OPTIONS:

1. RECOMMENDED: Create a .env file (works in terminal AND PyCharm):
   Create a file named '.env' in your project directory with:
   AI_API_KEY=your-openai-api-key-here

2. ENVIRONMENT VARIABLE (current session only):
{env_commands}

3. PERMANENT ENVIRONMENT VARIABLE:
{permanent_commands}

4. PYCHARM IDE CONFIGURATION:
   • Run/Debug Configurations → Environment variables
   • Add: AI_API_KEY=your-openai-api-key-here

5. DIRECT OVERRIDE (for tests/one-off usage):
   create_client(api_key="your-openai-api-key-here")
   # or
   AiSettings(api_key="your-openai-api-key-here")

PRECEDENCE ORDER:
1. Explicit api_key parameter (highest priority)
2. AI_API_KEY environment variable
3. .env file in project directory
4. System environment variables

FILE LOCATIONS CHECKED:
• Current working directory: {Path.cwd()}/.env
• Environment variables: AI_API_KEY
• System environment

TIP: The .env method is recommended for local development as it works
   seamlessly across terminals, IDEs, and different operating systems.

After setup, restart your terminal or IDE and try again.
"""
        
        return message


def resolve_api_key(
    explicit_api_key: Optional[str] = None,
    settings_api_key: Optional[str] = None,
    env_file: Optional[str] = ".env"
) -> str:
    """
    Resolve API key from multiple sources with proper precedence.
    
    Args:
        explicit_api_key: Direct API key parameter (highest priority)
        settings_api_key: API key from settings object
        env_file: Path to .env file (default: ".env")
        
    Returns:
        Resolved API key
        
    Raises:
        MissingApiKeyError: If no API key found in any location
    """
    
    # 1. Check explicit parameter (highest priority)
    if explicit_api_key:
        stripped_key = explicit_api_key.strip()
        if stripped_key:
            return stripped_key
    
    # 2. Check settings object
    if settings_api_key:
        stripped_key = settings_api_key.strip()
        if stripped_key:
            return stripped_key
    
    # 3. Check environment variable
    env_key = os.getenv("AI_API_KEY")
    if env_key:
        stripped_key = env_key.strip()
        if stripped_key:
            return stripped_key
    
    # 4. Check .env file
    if env_file:
        env_path = Path(env_file)
        if env_path.exists():
            try:
                # Read .env file manually to avoid import issues
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('AI_API_KEY='):
                            key_value = line[11:].strip()  # Remove 'AI_API_KEY='
                            if key_value and key_value != 'your-key-here':
                                return key_value
            except (IOError, OSError):
                # Silently ignore .env read errors (file not found, permission issues)
                pass
    
    # 5. No API key found - raise helpful error
    raise MissingApiKeyError()
