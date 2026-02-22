"""Interactive setup wizard for v1.0.1 provider configuration.

Provides cross-platform interactive setup with multi-provider support,
optional dependency detection, and proper .env file handling.
"""

import importlib.util
import sys
import time
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any

from .env_writer import EnvWriter


class SetupMode(Enum):
    """Setup mode options."""
    SINGLE_PROVIDER = "single-provider"
    MULTI_PROVIDER = "multi-provider"
    NON_INTERACTIVE = "non-interactive"
    
    # Legacy values for backward compatibility
    NORMAL = "normal"  # Maps to single-provider
    ENHANCED = "enhanced"  # Maps to multi-provider
    IMPROVED = "improved"  # Maps to non-interactive


@dataclass
class SetupResult:
    """Result of setup wizard execution."""
    provider: str
    auto_select_order: Optional[List[str]]
    providers: Dict[str, Dict[str, Any]]
    dotenv_path: Path
    backup_created: bool = False
    
    @property
    def api_key(self) -> Optional[str]:
        """Get API key for backward compatibility."""
        if self.provider == "auto":
            return None
        provider_config = self.providers.get(self.provider, {})
        return provider_config.get("api_key")
    
    @property
    def model(self) -> Optional[str]:
        """Get model for backward compatibility."""
        if self.provider == "auto":
            return None
        provider_config = self.providers.get(self.provider, {})
        return provider_config.get("model")
    
    @property
    def base_url(self) -> Optional[str]:
        """Get base URL for backward compatibility."""
        if self.provider == "auto":
            return None
        provider_config = self.providers.get(self.provider, {})
        return provider_config.get("base_url")


@dataclass
class ProbeResult:
    """Result of connectivity probe."""
    success: bool
    provider: str
    base_url: str
    message: str
    response_time_ms: Optional[float] = None
    status_code: Optional[int] = None


class SetupWizard:
    """Interactive setup wizard for ai_utilities configuration."""
    
    def __init__(self, allow_network: bool = False):
        """Initialize the setup wizard.
        
        Args:
            allow_network: Whether to allow network connectivity checks (default: False)
        """
        self.allow_network = allow_network
        self.env_writer = EnvWriter()
        
        # Provider configurations aligned with test expectations
        self.providers = {
            "ollama": {
                "name": "Ollama",
                "description": "Local Ollama server",
                "default_model": None,  # User must specify
                "requires_api_key": False,
                "default_base_url": "http://localhost:11434/v1",
                "optional_deps": []
            },
            "groq": {
                "name": "Groq",
                "description": "Fast inference with Groq API",
                "default_model": "llama3-70b-8192",
                "requires_api_key": True,
                "default_base_url": "https://api.groq.com/openai/v1",
                "optional_deps": []
            },
            "together": {
                "name": "Together AI",
                "description": "Open source models via Together AI",
                "default_model": "meta-llama/Llama-3-8b-chat-hf",
                "requires_api_key": True,
                "default_base_url": "https://api.together.xyz/v1",
                "optional_deps": []
            },
            "openrouter": {
                "name": "OpenRouter",
                "description": "Access to multiple models via OpenRouter",
                "default_model": "meta-llama/llama-3-8b-instruct:free",
                "requires_api_key": True,
                "default_base_url": "https://openrouter.ai/api/v1",
                "optional_deps": []
            },
            "deepseek": {
                "name": "DeepSeek",
                "description": "DeepSeek AI models",
                "default_model": "deepseek-chat",
                "requires_api_key": True,
                "default_base_url": "https://api.deepseek.com/v1",
                "optional_deps": []
            },
            "openai": {
                "name": "OpenAI",
                "description": "Official OpenAI API (GPT-4, GPT-3.5)",
                "default_model": "gpt-4o-mini",
                "requires_api_key": True,
                "default_base_url": "https://api.openai.com/v1",
                "optional_deps": ["openai"]
            },
            "lmstudio": {
                "name": "LM Studio",
                "description": "Local LM Studio server",
                "default_model": None,  # User must specify
                "requires_api_key": False,
                "default_base_url": "http://localhost:1234/v1",
                "optional_deps": []
            },
            "fastchat": {
                "name": "FastChat",
                "description": "Local FastChat server",
                "default_model": None,  # User must specify
                "requires_api_key": False,
                "default_base_url": "http://localhost:8000/v1",
                "optional_deps": []
            },
            "text-generation-webui": {
                "name": "Text Generation WebUI",
                "description": "Local Text Generation WebUI",
                "default_model": None,  # User must specify
                "requires_api_key": False,
                "default_base_url": "http://localhost:5000/v1",
                "optional_deps": []
            }
        }
        
        # Default auto-select order (local providers first)
        self.default_auto_order = [
            "ollama", "lmstudio", "groq", "openrouter", 
            "together", "deepseek", "openai"
        ]
    
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
    
    def _prompt_choice(self, message: str, choices: List[str], default: Optional[str] = None, allow_n_response: bool = False, allow_done_response: bool = False) -> str:
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
                
                # Handle special 'n' response for provider selection
                if allow_n_response and response.lower() == 'n':
                    return 'n'
                
                # Handle special 'done' response for provider selection
                if allow_done_response and response.lower() == 'done':
                    return 'done'
                
                try:
                    index = int(response) - 1
                    if 0 <= index < len(choices):
                        return choices[index]
                except ValueError:
                    pass
                
                print(f"Please enter a number between 1 and {len(choices)}")
            except (EOFError, KeyboardInterrupt):
                raise
    
    def _prompt_yes_no(self, message: str, default: bool = True) -> bool:
        """Prompt user for yes/no response."""
        default_str = "Y/n" if default else "y/N"
        while True:
            try:
                response = input(f"{message} [{default_str}]: ").strip().lower()
                if not response:
                    return default
                if response in ['y', 'yes']:
                    return True
                if response in ['n', 'no']:
                    return False
                print("Please enter 'y' or 'n'")
            except (EOFError, KeyboardInterrupt):
                raise
    
    def _select_setup_mode(self) -> SetupMode:
        """Select setup mode."""
        if not self._is_interactive():
            raise RuntimeError("Setup mode selection requires interactive environment")
        
        print("=== AI Utilities Setup Wizard ===\n")
        print("Choose setup mode:")
        
        modes = [
            ("normal", "Configure a single AI provider (default)"),
            ("enhanced", "Configure multiple providers with auto-selection"),
            ("improved", "Non-interactive single provider setup"),
            ("single-provider", "Configure a single AI provider"),
            ("multi-provider", "Configure multiple providers with auto-selection"),
        ]
        
        choice = self._prompt_choice(
            "Setup mode:",
            [f"{name} - {desc}" for name, desc in modes],
            "normal - Configure a single AI provider (default)"
        )
        
        mode_name = choice.split(" - ")[0]
        return SetupMode(mode_name)
    
    def _select_providers(self) -> List[str]:
        """Select providers for multi-provider mode."""
        if not self._is_interactive():
            raise RuntimeError("Provider selection requires interactive environment")
        selected_providers: List[str] = []
        providers_config: Dict[str, Dict[str, str]] = {}
        available_providers = list(self.providers.keys())
        
        while True:
            print(f"\nCurrently selected: {', '.join(selected_providers) if selected_providers else 'None'}")
            
            # Show all providers with stable numbering, marking already selected ones
            choices = []
            for i, provider_key in enumerate(available_providers):
                info = self.providers[provider_key]
                if isinstance(info, dict):
                    if provider_key in selected_providers:
                        choices.append(f"{info['name']} - {info['description']} (already selected)")
                    else:
                        choices.append(f"{info['name']} - {info['description']}")
            
            choices.append("Done selecting providers")
            
            choice = self._prompt_choice(
                "Add provider (or 'Done' when finished):",
                choices,
                allow_n_response=True,
                allow_done_response=True
            )
            
            # Handle special case for 'n' or 'done' to stop adding providers
            if choice.lower() in ['n', 'done'] or choice == "Done selecting providers":
                break
            
            # Find the provider key from the choice
            for i, provider_key in enumerate(available_providers):
                info = self.providers[provider_key]
                if isinstance(info, dict):
                    choice_text = f"{info['name']} - {info['description']}"
                    if choice == choice_text or choice.startswith(choice_text):
                        if provider_key in selected_providers:
                            print(f"{provider_key} is already selected. Please choose a different provider.")
                        else:
                            selected_providers.append(provider_key)
                            # Configure provider immediately after selection
                            providers_config[provider_key] = self._configure_provider(provider_key)
                        break
        
        # Store the configurations for later use
        self._temp_providers_config = providers_config
        return selected_providers
    
    def _configure_provider(self, provider_key: str) -> Dict[str, Any]:
        """Configure a single provider."""
        provider_info = self.providers[provider_key]
        
        if not isinstance(provider_info, dict):
            raise ValueError(f"Provider info for {provider_key} must be a dictionary")
        
        print(f"\n=== {provider_info['name']} Configuration ===")
        
        config = {
            "base_url": provider_info.get("base_url", ""),
            "model": provider_info.get("default_model", ""),
            "api_key": None
        }
        
        # API key
        if provider_info.get("requires_api_key", False):
            env_var = f"{provider_key.upper()}_API_KEY"
            print(f"Get your API key from the {provider_info['name']} dashboard")
            print(f"You can also set environment variable: {env_var}")
            
            # Check if already set in environment
            import os
            existing_key = os.getenv(env_var) or os.getenv("AI_API_KEY")
            if existing_key:
                use_existing = self._prompt_yes_no(
                    f"Use existing API key ({'*' * 8}{existing_key[-4:] if len(existing_key) > 4 else '****'})?",
                    default=True
                )
                if use_existing:
                    config["api_key"] = existing_key
                else:
                    config["api_key"] = self._prompt("Enter API key")
            else:
                config["api_key"] = self._prompt("Enter API key")
        
        # Base URL (for custom endpoints)
        if provider_key in ["ollama", "lmstudio", "fastchat", "text-generation-webui"]:
            print(f"Default URL: {config['base_url']}")
            custom_url = self._prompt("Base URL (press Enter for default)", config["base_url"])
            if custom_url:
                config["base_url"] = custom_url
        
        # Model (required for local providers)
        if not config["model"] or provider_key in ["ollama", "lmstudio", "fastchat", "text-generation-webui"]:
            if provider_key == "ollama":
                print("Examples: llama3, llama3.1, codellama, mistral")
            elif provider_key == "lmstudio":
                print("Use the model name as shown in LM Studio")
            elif provider_key == "fastchat":
                print("Enter the model name configured in FastChat")
            elif provider_key == "text-generation-webui":
                print("Enter the model name loaded in Text Generation WebUI")
            
            config["model"] = self._prompt("Model name", config.get("model"))
        
        return config
    
    def _get_auto_select_order(self, selected_providers: List[str]) -> List[str]:
        """Get auto-select order for multi-provider mode."""
        if not self._is_interactive():
            # Use default order with selected providers filtered
            return [p for p in self.default_auto_order if p in selected_providers]
        
        print(f"\n=== Provider Auto-Selection Order ===")
        print("Providers will be tried in this order until one works:")
        
        # Start with selected providers in default order
        ordered_providers = [p for p in self.default_auto_order if p in selected_providers]
        
        # Add any remaining selected providers
        for provider in selected_providers:
            if provider not in ordered_providers:
                ordered_providers.append(provider)
        
        print(f"Default order: {', '.join(ordered_providers)}")
        
        use_default = self._prompt_yes_no("Use default order?", default=True)
        if use_default:
            return ordered_providers
        
        # Let user customize order
        print("Customize the order (providers will be tried from top to bottom):")
        custom_order: List[str] = []
        remaining_providers = ordered_providers.copy()
        
        while remaining_providers:
            print(f"\nCurrent order: {', '.join(custom_order) if custom_order else 'None'}")
            print("Remaining providers:")
            
            for i, provider in enumerate(remaining_providers, 1):
                info = self.providers[provider]
                if isinstance(info, dict):
                    print(f"  {i}. {info['name']}")
            
            # Build choice list properly
            provider_choices = []
            for p in remaining_providers:
                provider_info = self.providers[p]
                if isinstance(provider_info, dict):
                    name = provider_info.get('name')
                    if isinstance(name, str):
                        provider_choices.append(name)
            provider_choices.append("Done ordering")
            
            choice = self._prompt_choice(
                "Select next provider (or 'Done' if finished):",
                provider_choices,
                allow_done_response=True
            )
            
            if choice == "Done ordering" or choice.lower() == 'done':
                if not custom_order:
                    print("You must select at least one provider")
                    continue
                break
            
            # Find provider from choice
            for provider in remaining_providers:
                provider_info = self.providers[provider]
                if isinstance(provider_info, dict) and choice == provider_info['name']:
                    custom_order.append(provider)
                    remaining_providers.remove(provider)
                    break
        
        return custom_order
    
    def check_optional_dependencies(self, providers: List[str]) -> None:
        """Check for optional dependencies and provide install guidance."""
        missing_deps = set()
        
        for provider_key in providers:
            provider_info = self.providers[provider_key]
            if isinstance(provider_info, dict):
                for dep in provider_info.get("optional_deps", []):
                    if importlib.util.find_spec(dep) is None:
                        missing_deps.add(dep)
        
        if missing_deps:
            print(f"\n=== Optional Dependencies ===")
            print("The following optional dependencies are missing for full functionality:")
            
            for dep in sorted(missing_deps):
                install_cmd = f'python -m pip install "ai-utilities[{dep}]"'
                print(f"\n{dep}:")
                print(f"  Install with: {install_cmd}")
            
            print(f"\nNote: These dependencies are optional. The library will work without them,")
            print(f"      but some features may be limited.")
    
    def run_interactive_setup(self, dotenv_path: Path) -> SetupResult:
        """Run interactive setup wizard."""
        if not self._is_interactive():
            raise RuntimeError("Interactive setup requires TTY")
        
        # Select setup mode
        mode = self._select_setup_mode()
        
        # Handle legacy modes
        if mode == SetupMode.NORMAL:
            mode = SetupMode.SINGLE_PROVIDER
        elif mode == SetupMode.ENHANCED:
            mode = SetupMode.MULTI_PROVIDER
        elif mode == SetupMode.IMPROVED:
            mode = SetupMode.SINGLE_PROVIDER  # Treat improved as single provider
        
        if mode == SetupMode.SINGLE_PROVIDER:
            return self._run_single_provider_setup(dotenv_path)
        elif mode == SetupMode.MULTI_PROVIDER:
            return self._run_multi_provider_setup(dotenv_path)
        else:
            raise ValueError(f"Unsupported setup mode: {mode}")
    
    def _run_single_provider_setup(self, dotenv_path: Path) -> SetupResult:
        """Run single provider setup."""
        print(f"\n=== Single Provider Setup ===")
        
        # Select provider
        provider_choices = []
        for key, info in self.providers.items():
            if isinstance(info, dict):
                provider_choices.append(f"{info['name']} - {info['description']}")
        
        choice = self._prompt_choice(
            "Select AI provider:",
            provider_choices,
            "OpenAI - Official OpenAI API (GPT-4, GPT-3.5)"
        )
        
        # Find the provider key from the choice
        provider_key = None
        for key, info in self.providers.items():
            if isinstance(info, dict) and choice.startswith(info['name']):
                provider_key = key
                break
        
        if not provider_key:
            raise RuntimeError("Invalid provider selection")
        
        # Configure provider
        provider_config = self._configure_provider(provider_key)
        
        # Check optional dependencies
        self.check_optional_dependencies([provider_key])
        
        # Optional connectivity probing in interactive mode
        if self._is_interactive() and provider_config.get("api_key"):
            probe_result = self._optional_probe_after_configuration(provider_key, provider_config)
            if probe_result and not probe_result.success:
                print(f"⚠️  {probe_result.message}")
        
        # Ask about writing API keys
        write_keys = True
        if provider_config.get("api_key"):
            write_keys = self._prompt_yes_no(
                "Write API key to .env file? (Recommended for development)",
                default=True
            )
            if not write_keys:
                # Don't write API key, but show environment variable instructions
                self._show_env_instructions(provider_key, provider_config["api_key"])
                provider_config["api_key"] = None
        
        # Create configuration
        config = {
            "provider": provider_key,
            **provider_config
        }
        
        # Write .env file
        backup_existed = dotenv_path.exists()
        self.env_writer.create_or_patch(dotenv_path, config)
        
        return SetupResult(
            provider=provider_key,
            auto_select_order=None,
            providers={provider_key: provider_config},
            dotenv_path=dotenv_path,
            backup_created=backup_existed
        )
    
    def _run_multi_provider_setup(self, dotenv_path: Path) -> SetupResult:
        """Run multi-provider setup."""
        print(f"\n=== Multi-Provider Setup ===")
        
        # Select providers (this now also configures them)
        selected_providers = self._select_providers()
        
        if not selected_providers:
            raise ValueError("At least one provider must be selected")
        
        # Use the pre-configured providers from _select_providers
        providers_config = getattr(self, '_temp_providers_config', {})
        
        # Get auto-select order
        auto_order = self._get_auto_select_order(selected_providers)
        
        # Check optional dependencies
        self.check_optional_dependencies(selected_providers)
        
        # Optional connectivity probing in interactive mode
        if self._is_interactive():
            self._probe_multiple_providers(providers_config)
        
        # Ask about writing API keys
        write_keys = self._prompt_yes_no(
            "Write API keys to .env file? (Recommended for development)",
            default=True
        )
        
        if not write_keys:
            # Remove API keys from config and show instructions
            for provider_key, config in providers_config.items():
                if config.get("api_key"):
                    self._show_env_instructions(provider_key, config["api_key"])
                    config["api_key"] = None
        
        # Create configuration
        config = {
            "provider": "auto",
            "auto_select_order": auto_order,
            "providers": providers_config
        }
        
        # Write .env file
        backup_existed = dotenv_path.exists()
        self.env_writer.create_or_patch(dotenv_path, config)
        
        return SetupResult(
            provider="auto",
            auto_select_order=auto_order,
            providers=providers_config,
            dotenv_path=dotenv_path,
            backup_created=backup_existed
        )
    
    def _show_env_instructions(self, provider_key: str, api_key: str) -> None:
        """Show environment variable setup instructions."""
        env_var = f"{provider_key.upper()}_API_KEY"
        masked_key = f"{'*' * 8}{api_key[-4:]}" if len(api_key) > 4 else "****"
        
        print(f"\n=== Environment Variable Setup ===")
        print(f"To use {provider_key} without writing to .env, set:")
        print()
        print(f"Current session only:")
        print(f"  Windows PowerShell: $env:{env_var}=\"{masked_key}\"")
        print(f"  macOS/Linux: export {env_var}=\"{masked_key}\"")
        print()
        print(f"Permanent setup:")
        print(f"  Add to your shell profile (.bashrc, .zshrc, etc.)")
        print(f"  export {env_var}=\"your-actual-api-key\"")
    
    def run_non_interactive_setup(
        self, 
        dotenv_path: Path, 
        mode: Optional[SetupMode] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> SetupResult:
        """Run non-interactive setup with specified parameters."""
        if not mode:
            raise ValueError("Mode must be specified in non-interactive mode")
        
        if mode == SetupMode.SINGLE_PROVIDER or mode == SetupMode.NORMAL:
            if not provider:
                raise ValueError("Provider must be specified for single provider mode")
            
            provider_info = self.providers[provider]
            if not isinstance(provider_info, dict):
                raise ValueError(f"Provider info for {provider} must be a dictionary")
            
            config = {
                "provider": provider,
                "base_url": base_url or provider_info.get("base_url", ""),
                "model": model or provider_info.get("default_model", ""),
                "api_key": api_key
            }
            
            backup_existed = dotenv_path.exists()
            self.env_writer.create_or_patch(dotenv_path, config)
            
            return SetupResult(
                provider=provider,
                auto_select_order=None,
                providers={provider: config},
                dotenv_path=dotenv_path,
                backup_created=backup_existed
            )
        
        elif mode == SetupMode.MULTI_PROVIDER or mode == SetupMode.ENHANCED:
            # For now, treat enhanced mode as not implemented in non-interactive
            raise ValueError(f"Non-interactive mode {mode} not yet implemented")
        
        elif mode == SetupMode.NON_INTERACTIVE or mode == SetupMode.IMPROVED:
            # Treat improved as non-interactive single provider if provider specified
            if not provider:
                raise ValueError("Provider must be specified for improved mode")
            
            provider_info = self.providers[provider]
            if not isinstance(provider_info, dict):
                raise ValueError(f"Provider info for {provider} must be a dictionary")
            
            config = {
                "provider": provider,
                "base_url": base_url or provider_info.get("base_url", ""),
                "model": model or provider_info.get("default_model", ""),
                "api_key": api_key
            }
            
            backup_existed = dotenv_path.exists()
            self.env_writer.create_or_patch(dotenv_path, config)
            
            return SetupResult(
                provider=provider,
                auto_select_order=None,
                providers={provider: config},
                dotenv_path=dotenv_path,
                backup_created=backup_existed
            )
        
        else:
            raise ValueError(f"Non-interactive mode {mode} not yet implemented")
    
    def _probe_connection(self, provider: str, base_url: str, api_key: Optional[str] = None) -> ProbeResult:
        """Dispatch connection probe based on provider type."""
        if not self.allow_network:
            return ProbeResult(
                success=False,
                provider=provider,
                base_url=base_url,
                message="Network connections blocked by default. Use --allow-network or --run-integration to enable."
            )
        
        try:
            if provider in ["openai", "groq", "together", "openrouter", "deepseek"]:
                # Ensure api_key is not None for _probe_hosted
                if api_key is None:
                    return ProbeResult(
                        success=False,
                        provider=provider,
                        base_url=base_url,
                        message="API key required for connection probe"
                    )
                return self._probe_hosted(provider, base_url, api_key)
            elif provider == "ollama":
                return self._probe_ollama(base_url)
            else:
                return self._probe_generic(base_url)
        except Exception as e:
            return ProbeResult(
                success=False,
                provider=provider,
                base_url=base_url,
                message=f"Probe failed: {str(e)}"
            )
    
    def _probe_hosted(self, provider: str, base_url: str, api_key: str) -> ProbeResult:
        """Probe hosted provider using /models endpoint."""
        try:
            import requests
            
            start_time = time.time()
            response = requests.get(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=3
            )
            response_time_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return ProbeResult(
                    success=True,
                    provider=provider,
                    base_url=base_url,
                    message=f"Connected to {provider} successfully",
                    response_time_ms=response_time_ms,
                    status_code=response.status_code
                )
            elif response.status_code == 401:
                return ProbeResult(
                    success=False,
                    provider=provider,
                    base_url=base_url,
                    message=f"Authentication failed for {provider} - check API key",
                    response_time_ms=response_time_ms,
                    status_code=response.status_code
                )
            else:
                return ProbeResult(
                    success=False,
                    provider=provider,
                    base_url=base_url,
                    message=f"{provider} returned status {response.status_code}",
                    response_time_ms=response_time_ms,
                    status_code=response.status_code
                )
        except Exception as e:
            return ProbeResult(
                success=False,
                provider=provider,
                base_url=base_url,
                message=f"Failed to connect to {provider}: {str(e)}"
            )
    
    def _probe_ollama(self, base_url: str) -> ProbeResult:
        """Probe Ollama using /api/tags endpoint."""
        try:
            import requests
            
            start_time = time.time()
            response = requests.get(f"{base_url}/api/tags", timeout=3)
            response_time_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return ProbeResult(
                    success=True,
                    provider="ollama",
                    base_url=base_url,
                    message="Connected to Ollama successfully",
                    response_time_ms=response_time_ms,
                    status_code=response.status_code
                )
            else:
                return ProbeResult(
                    success=False,
                    provider="ollama",
                    base_url=base_url,
                    message=f"Ollama returned status {response.status_code}",
                    response_time_ms=response_time_ms,
                    status_code=response.status_code
                )
        except Exception as e:
            return ProbeResult(
                success=False,
                provider="ollama",
                base_url=base_url,
                message=f"Failed to connect to Ollama: {str(e)}"
            )
    
    def _probe_generic(self, base_url: str) -> ProbeResult:
        """Probe generic endpoint with minimal GET request."""
        try:
            import requests
            
            start_time = time.time()
            response = requests.get(base_url, timeout=3)
            response_time_ms = (time.time() - start_time) * 1000
            
            if response.status_code < 500:
                return ProbeResult(
                    success=True,
                    provider="generic",
                    base_url=base_url,
                    message="Connected successfully",
                    response_time_ms=response_time_ms,
                    status_code=response.status_code
                )
            else:
                return ProbeResult(
                    success=False,
                    provider="generic",
                    base_url=base_url,
                    message=f"Server error: {response.status_code}",
                    response_time_ms=response_time_ms,
                    status_code=response.status_code
                )
        except Exception as e:
            return ProbeResult(
                success=False,
                provider="generic",
                base_url=base_url,
                message=f"Connection failed: {str(e)}"
            )
    
    def _optional_probe_after_configuration(self, provider_key: str, provider_config: Dict[str, Any]) -> Optional[ProbeResult]:
        """Offer optional connectivity probing after provider configuration."""
        if not self._is_interactive():
            return None
            
        # Ask user if they want to probe connectivity
        want_probe = self._prompt_yes_no(
            "Test connectivity to provider? (Optional, no API calls will be made)",
            default=False
        )
        
        if not want_probe:
            return None
        
        print(f"Testing connectivity to {provider_key}...")
        result = self._probe_connection(
            provider_key,
            provider_config["base_url"],
            provider_config.get("api_key")
        )
        
        # Print user-friendly message
        if result.success:
            time_str = f" ({result.response_time_ms:.0f}ms)" if result.response_time_ms else ""
            print(f"✅ {result.message}{time_str}")
        else:
            print(f"❌ {result.message}")
        
        return result
    
    def _probe_multiple_providers(self, providers_config: Dict[str, Dict[str, Any]]) -> None:
        """Probe multiple providers and show results."""
        if not self._is_interactive() or not providers_config:
            return
        
        # Ask user if they want to probe connectivity
        want_probe = self._prompt_yes_no(
            "Test connectivity to all configured providers? (Optional)",
            default=False
        )
        
        if not want_probe:
            return
        
        print("\n=== Connectivity Test Results ===")
        
        for provider_key, config in providers_config.items():
            print(f"\nTesting {provider_key}...", end=" ")
            
            result = self._probe_connection(
                provider_key,
                config["base_url"],
                config.get("api_key")
            )
            
            if result.success:
                time_str = f" ({result.response_time_ms:.0f}ms)" if result.response_time_ms else ""
                print(f"✅ Success{time_str}")
            else:
                print(f"❌ Failed")
                print(f"   {result.message}")


def run_setup_wizard(
    dotenv_path: str = ".env",
    mode: Optional[SetupMode] = None,
    non_interactive: bool = False,
    allow_network: bool = False,
    **kwargs
) -> SetupResult:
    """Run the setup wizard (convenience function).
    
    Args:
        dotenv_path: Path to .env file
        mode: Setup mode (None to prompt)
        non_interactive: Run without prompts
        allow_network: Whether to allow network connectivity checks
        **kwargs: Additional parameters for non-interactive mode
        
    Returns:
        SetupResult with configuration
    """
    wizard = SetupWizard(allow_network=allow_network)
    path = Path(dotenv_path)
    
    if non_interactive:
        return wizard.run_non_interactive_setup(path, mode, **kwargs)
    else:
        return wizard.run_interactive_setup(path)
