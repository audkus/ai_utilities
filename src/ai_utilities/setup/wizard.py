"""Interactive setup wizard for ai_utilities configuration."""

import os
import sys
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Tuple


class SetupMode(Enum):
    """Setup mode options."""
    NORMAL = "normal"
    ENHANCED = "enhanced"
    IMPROVED = "improved"


@dataclass
class SetupResult:
    """Result of setup wizard execution."""
    provider: str
    api_key: Optional[str]
    base_url: Optional[str]
    model: Optional[str]
    dotenv_lines: List[str]


class SetupWizard:
    """Interactive setup wizard for ai_utilities configuration."""
    
    def __init__(self):
        self.providers = {
            "openai": {
                "name": "OpenAI",
                "description": "Official OpenAI API (GPT-4, GPT-3.5)",
                "default_model": "gpt-3.5-turbo",
                "requires_api_key": True,
                "base_url": "https://api.openai.com/v1"
            },
            "groq": {
                "name": "Groq",
                "description": "Fast inference with Groq API",
                "default_model": "llama3-70b-8192",
                "requires_api_key": True,
                "base_url": "https://api.groq.com/openai/v1"
            },
            "together": {
                "name": "Together AI",
                "description": "Open source models via Together AI",
                "default_model": "meta-llama/Llama-3-8b-chat-hf",
                "requires_api_key": True,
                "base_url": "https://api.together.xyz/v1"
            },
            "openrouter": {
                "name": "OpenRouter",
                "description": "Access to multiple models via OpenRouter",
                "default_model": "meta-llama/llama-3-8b-instruct:free",
                "requires_api_key": True,
                "base_url": "https://openrouter.ai/api/v1"
            },
            "openai_compatible": {
                "name": "OpenAI Compatible",
                "description": "Custom OpenAI-compatible endpoint",
                "default_model": None,
                "requires_api_key": False,
                "base_url": None
            },
            "ollama": {
                "name": "Ollama",
                "description": "Local Ollama server",
                "default_model": None,
                "requires_api_key": False,
                "base_url": "http://localhost:11434/v1"
            }
        }
    
    def _is_interactive(self) -> bool:
        """Check if we're in an interactive environment."""
        return sys.stdin.isatty()
    
    def _prompt(self, message: str, default: Optional[str] = None) -> str:
        """Prompt user for input with optional default."""
        if default:
            prompt = f"{message} [{default}]: "
        else:
            prompt = f"{message}: "
        
        try:
            response = input(prompt).strip()
            return response if response else (default or "")
        except (EOFError, KeyboardInterrupt):
            raise
    
    def _prompt_choice(self, message: str, choices: List[str], default: Optional[str] = None) -> str:
        """Prompt user to choose from a list."""
        if not choices:
            raise ValueError("Choices list cannot be empty")
        
        print(f"\n{message}")
        for i, choice in enumerate(choices, 1):
            marker = " (default)" if choice == default else ""
            print(f"  {i}. {choice}{marker}")
        
        while True:
            try:
                response = input(f"\nEnter choice (1-{len(choices)})").strip()
                if not response and default:
                    return default
                
                try:
                    index = int(response) - 1
                    if 0 <= index < len(choices):
                        return choices[index]
                except ValueError:
                    pass
                
                print(f"Please enter a number between 1 and {len(choices)}")
            except (EOFError, KeyboardInterrupt):
                raise
    
    def _select_mode(self, mode: Optional[SetupMode]) -> SetupMode:
        """Select setup mode."""
        if mode:
            return mode
        
        if not self._is_interactive():
            raise RuntimeError("Mode selection requires interactive environment")
        
        print("=== AI Utilities Setup Wizard ===\n")
        print("Choose setup mode:")
        
        modes = [
            ("normal", "Quick setup with essential configuration"),
            ("enhanced", "Guided setup with explanations and choices"),
            ("improved", "Advanced options for local endpoints and custom configurations")
        ]
        
        choice = self._prompt_choice(
            "Setup mode:",
            [f"{name} - {desc}" for name, desc in modes],
            "normal - Quick setup with essential configuration"
        )
        
        mode_name = choice.split(" - ")[0]
        return SetupMode(mode_name)
    
    def _select_provider(self, mode: SetupMode) -> str:
        """Select provider based on mode."""
        if mode == SetupMode.NORMAL:
            # Normal mode defaults to OpenAI
            return "openai"
        
        if not self._is_interactive():
            raise RuntimeError("Provider selection requires interactive environment")
        
        print(f"\nSelect AI provider:")
        
        provider_choices = []
        for key, info in self.providers.items():
            provider_choices.append(f"{info['name']} - {info['description']}")
        
        choice = self._prompt_choice(
            "Provider:",
            provider_choices,
            "OpenAI - Official OpenAI API (GPT-4, GPT-3.5)"
        )
        
        # Find the provider key from the choice
        for key, info in self.providers.items():
            if choice.startswith(info['name']):
                return key
        
        raise RuntimeError("Invalid provider selection")
    
    def _get_api_key(self, provider: str, mode: SetupMode) -> Optional[str]:
        """Get API key for provider."""
        provider_info = self.providers[provider]
        
        if not provider_info["requires_api_key"]:
            return None
        
        if mode == SetupMode.NORMAL:
            # Normal mode prompts for API key
            if not self._is_interactive():
                raise RuntimeError("API key input requires interactive environment")
            
            env_var = f"{provider.upper()}_API_KEY"
            print(f"\nEnter API key for {provider_info['name']}:")
            print(f"(You can also set environment variable {env_var})")
            
            return self._prompt(f"API key")
        
        # Enhanced/improved modes provide more guidance
        if not self._is_interactive():
            raise RuntimeError("API key input requires interactive environment")
        
        env_var = f"{provider.upper()}_API_KEY"
        print(f"\n=== API Key for {provider_info['name']} ===")
        print(f"Get your API key from the {provider_info['name']} dashboard")
        print(f"You can also set environment variable: {env_var}")
        
        return self._prompt(f"API key")
    
    def _get_base_url(self, provider: str, mode: SetupMode) -> Optional[str]:
        """Get base URL for provider."""
        provider_info = self.providers[provider]
        
        if provider in ["openai", "groq", "together", "openrouter"]:
            # These have fixed base URLs
            return provider_info["base_url"]
        
        if provider in ["ollama"]:
            # Local provider with default URL
            if mode == SetupMode.NORMAL:
                return provider_info["base_url"]
            
            if not self._is_interactive():
                return provider_info["base_url"]
            
            print(f"\n=== {provider_info['name']} Configuration ===")
            print(f"Default URL: {provider_info['base_url']}")
            
            return self._prompt("Base URL", provider_info["base_url"])
        
        if provider == "openai_compatible":
            # Custom endpoint - always prompt
            if not self._is_interactive():
                raise RuntimeError("Base URL input requires interactive environment")
            
            print(f"\n=== OpenAI Compatible Endpoint ===")
            print("Enter the base URL for your OpenAI-compatible API")
            
            return self._prompt("Base URL")
        
        return None
    
    def _get_model(self, provider: str, mode: SetupMode, base_url: Optional[str]) -> Optional[str]:
        """Get model for provider."""
        provider_info = self.providers[provider]
        
        if provider_info["default_model"] and mode != SetupMode.IMPROVED:
            # Use default for normal/enhanced modes
            return provider_info["default_model"]
        
        if not self._is_interactive():
            if provider_info["default_model"]:
                return provider_info["default_model"]
            raise RuntimeError("Model selection requires interactive environment")
        
        print(f"\n=== Model Selection ===")
        
        if provider_info["default_model"]:
            default_model = provider_info["default_model"]
            print(f"Default model: {default_model}")
            return self._prompt("Model", default_model)
        else:
            print("Enter the model name for your provider")
            if provider == "ollama":
                print("Examples: llama3, codellama, mistral")
            elif provider == "openai_compatible":
                print("Use the model name as expected by your API")
            
            return self._prompt("Model")
    
    def _build_dotenv_content(self, result: SetupResult) -> List[str]:
        """Build .env file content from setup result."""
        lines = []
        
        # Add AI_PROVIDER
        lines.append(f"AI_PROVIDER={result.provider}")
        
        # Add AI_API_KEY if present
        if result.api_key:
            lines.append(f"AI_API_KEY={result.api_key}")
        
        # Add AI_BASE_URL if custom
        if result.base_url:
            provider_info = self.providers.get(result.provider, {})
            fixed_url = provider_info.get("base_url")
            if not fixed_url or result.base_url != fixed_url:
                lines.append(f"AI_BASE_URL={result.base_url}")
        
        # Add AI_MODEL if present
        if result.model:
            lines.append(f"AI_MODEL={result.model}")
        
        return lines
    
    def _read_existing_dotenv(self, dotenv_path: Path) -> Dict[str, str]:
        """Read existing .env file and return key-value pairs."""
        env_vars = {}
        
        if dotenv_path.exists():
            with open(dotenv_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        
        return env_vars
    
    def _write_dotenv(self, dotenv_path: Path, content: List[str], preserve_existing: bool = True) -> None:
        """Write content to .env file, optionally preserving existing entries."""
        if preserve_existing and dotenv_path.exists():
            # Read existing content
            existing_vars = self._read_existing_dotenv(dotenv_path)
            
            # Parse new content
            new_vars = {}
            for line in content:
                if '=' in line:
                    key, value = line.split('=', 1)
                    new_vars[key.strip()] = value.strip()
            
            # Merge: new vars override existing ones
            merged_vars = {**existing_vars, **new_vars}
            
            # Build final content
            final_lines = []
            for key, value in merged_vars.items():
                final_lines.append(f"{key}={value}")
            
            content = final_lines
        
        # Write file
        with open(dotenv_path, 'w') as f:
            for line in content:
                f.write(line + '\n')
    
    def run_wizard(
        self,
        mode: Optional[SetupMode] = None,
        dotenv_path: str = ".env",
        dry_run: bool = False,
        non_interactive: bool = False
    ) -> SetupResult:
        """Run the setup wizard.
        
        Args:
            mode: Setup mode (None to prompt)
            dotenv_path: Path to .env file
            dry_run: Print content without writing
            non_interactive: Run without prompts
            
        Returns:
            SetupResult with configuration
        """
        if non_interactive and not mode:
            raise ValueError("Mode must be specified in non-interactive mode")
        
        # Determine configuration
        selected_mode = mode or SetupMode.NORMAL
        
        if non_interactive:
            # Use defaults for non-interactive mode
            provider = "openai"
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AI_API_KEY")
            base_url = "https://api.openai.com/v1"
            model = "gpt-3.5-turbo"
        else:
            # Interactive mode
            selected_mode = self._select_mode(mode)
            provider = self._select_provider(selected_mode)
            api_key = self._get_api_key(provider, selected_mode)
            base_url = self._get_base_url(provider, selected_mode) or ""
            model = self._get_model(provider, selected_mode, base_url) or ""
        
        # Create result
        result = SetupResult(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            model=model,
            dotenv_lines=[]  # Will be filled below
        )
        
        # Build dotenv content
        result.dotenv_lines = self._build_dotenv_content(result)
        
        # Handle output
        if dry_run:
            print(f"\n=== Dry Run: .env content ===")
            for line in result.dotenv_lines:
                print(line)
        else:
            dotenv_file = Path(dotenv_path)
            self._write_dotenv(dotenv_file, result.dotenv_lines)
        
        return result


def run_setup_wizard(
    mode: Optional[SetupMode] = None,
    dotenv_path: str = ".env",
    dry_run: bool = False,
    non_interactive: bool = False
) -> SetupResult:
    """Run the setup wizard (convenience function).
    
    Args:
        mode: Setup mode (None to prompt)
        dotenv_path: Path to .env file
        dry_run: Print content without writing
        non_interactive: Run without prompts
        
    Returns:
        SetupResult with configuration
    """
    wizard = SetupWizard()
    return wizard.run_wizard(
        mode=mode,
        dotenv_path=dotenv_path,
        dry_run=dry_run,
        non_interactive=non_interactive
    )
