#!/usr/bin/env python3
"""
Improved Enhanced Setup System
Addressing user feedback about:
- Dynamic pricing information
- Outdated model names
- Multi-provider selection
- Environment variable handling
- Accurate parameter explanations
"""

import os
import platform
import getpass
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class AIProvider:
    """AI Provider configuration with future-proof descriptions"""
    name: str
    provider_id: str
    description: str
    api_key_env: str
    base_url_default: str
    model_categories: List[str]  # Instead of specific models
    setup_url: str
    cost_model: str  # Instead of specific pricing
    requires_extra_install: bool = True
    
    def get_user_friendly_info(self) -> str:
        """Return formatted provider information for users"""
        return f"""
{self.name}
   {self.description}
   
API Key Environment: {self.api_key_env}
Get API Key: {self.setup_url}
Cost Model: {self.cost_model}
Model Categories: {', '.join(self.model_categories)}

Installation: pip install "ai-utilities[{self.provider_id}]"
        """

class AIProviderRegistry:
    """Registry of supported AI providers with future-proof information"""
    
    def __init__(self):
        self.providers = {
            "openai": AIProvider(
                name="OpenAI",
                provider_id="openai",
                description="AI provider with GPT models, suitable for general tasks, coding, and creative writing.",
                api_key_env="OPENAI_API_KEY",
                base_url_default="https://api.openai.com/v1",
                model_categories=["GPT models", "Chat models", "Code models"],
                setup_url="https://platform.openai.com/api-keys",
                cost_model="Usage-based pricing (per token)",
                requires_extra_install=True
            ),
            "groq": AIProvider(
                name="Groq",
                provider_id="groq",
                description="AI provider with fast inference speeds, suitable for real-time applications and high-throughput use cases.",
                api_key_env="GROQ_API_KEY",
                base_url_default="https://api.groq.com/openai/v1",
                model_categories=["Open-source models", "Fast inference models"],
                setup_url="https://console.groq.com/keys",
                cost_model="Free tier available, then usage-based",
                requires_extra_install=False
            ),
            "together": AIProvider(
                name="Together AI",
                provider_id="together",
                description="AI provider with open-source models, suitable for specialized tasks and experimentation.",
                api_key_env="TOGETHER_API_KEY",
                base_url_default="https://api.together.xyz/v1",
                model_categories=["Open-source models", "Specialized models"],
                setup_url="https://api.together.xyz/settings/api-keys",
                cost_model="Usage-based pricing (varies by model)",
                requires_extra_install=False
            ),
            "anthropic": AIProvider(
                name="Anthropic Claude",
                provider_id="anthropic",
                description="AI provider with reasoning and safety features, suitable for complex analytical tasks.",
                api_key_env="ANTHROPIC_API_KEY",
                base_url_default="https://api.anthropic.com",
                model_categories=["Claude models", "Reasoning models"],
                setup_url="https://console.anthropic.com/",
                cost_model="Usage-based pricing (premium tier)",
                requires_extra_install=False
            ),
            "openrouter": AIProvider(
                name="OpenRouter",
                provider_id="openrouter",
                description="AI provider with access to multiple models through a single API, suitable for comparing model performance.",
                api_key_env="OPENROUTER_API_KEY",
                base_url_default="https://openrouter.ai/api/v1",
                model_categories=["Multiple provider models", "Comparison models"],
                setup_url="https://openrouter.ai/keys",
                cost_model="Usage-based pricing (varies by model)",
                requires_extra_install=False
            ),
            "ollama": AIProvider(
                name="Ollama",
                provider_id="ollama",
                description="Local AI provider that runs models on your machine, providing privacy and no API costs.",
                api_key_env="dummy-key",
                base_url_default="http://localhost:11434/v1",
                model_categories=["Local open-source models", "Private models"],
                setup_url="https://ollama.com/download",
                cost_model="Free (runs on your hardware)",
                requires_extra_install=False
            )
        }
    
    def get_provider(self, provider_id: str) -> Optional[AIProvider]:
        """Get provider by ID"""
        return self.providers.get(provider_id)
    
    def list_providers(self) -> List[AIProvider]:
        """Get all available providers"""
        return list(self.providers.values())
    
    def get_provider_menu(self) -> str:
        """Generate a formatted menu of providers with multi-select option"""
        menu = "\nAvailable AI Providers (Select one or multiple):"
        menu += "\n" + "=" * 60 + "\n"
        
        for i, (provider_id, provider) in enumerate(self.providers.items(), 1):
            menu += f"\n{i}. {provider.name}"
        
        menu += f"\n{len(self.providers) + 1}. All Providers (Configure multiple API keys)"
        menu += "\n" + "=" * 60
        menu += "\nEnter multiple numbers separated by commas (e.g., 1, 3, 5)"
        return menu
    
    def get_provider_installation_help(self, provider_ids: List[str]) -> str:
        """Get installation help for specific missing providers"""
        if not provider_ids:
            return ""
        
        help_text = "\nMissing provider support. Please install:\n\n"
        
        for provider_id in provider_ids:
            provider = self.get_provider(provider_id)
            if provider:
                help_text += f'pip install "ai-utilities[{provider_id}"]"\n'
        
        help_text += "\nProviders will be available immediately after installation.\n"
        return help_text

@dataclass
class ConfigurationParameter:
    """Configuration parameter with improved, accurate explanations"""
    name: str
    env_var: str
    description: str
    default_value: any
    value_type: type
    examples: List[str]
    how_to_choose: str
    
    def get_user_prompt(self) -> str:
        """Get user-friendly prompt for this parameter"""
        return f"""
{self.name}
   {self.description}
   
Environment Variable: {self.env_var}
Default: {self.default_value}
Examples: {', '.join(self.examples)}
How to choose: {self.how_to_choose}

Enter value (or press Enter for default {self.default_value}): """

class ConfigurationParameterRegistry:
    """Registry of configuration parameters with accurate explanations"""
    
    def __init__(self):
        self.parameters = {
            "model": ConfigurationParameter(
                name="AI Model",
                env_var="AI_MODEL",
                description="The specific AI model to use for generating responses. Different models have different capabilities, speeds, and costs.",
                default_value="gpt-3.5-turbo",
                value_type=str,
                examples=["gpt-4", "gpt-3.5-turbo", "claude-3-5-sonnet", "llama3.2:latest"],
                how_to_choose="Choose based on your needs: Advanced models for complex tasks, standard models for speed/cost efficiency, local models for privacy."
            ),
            "temperature": ConfigurationParameter(
                name="Temperature (Creativity)",
                env_var="AI_TEMPERATURE",
                description="Controls randomness in responses. Lower values = more focused/deterministic, Higher values = more creative/random.",
                default_value=0.7,
                value_type=float,
                examples=["0.0", "0.5", "0.7", "1.0", "1.5"],
                how_to_choose="Use 0.0-0.3 for factual responses, 0.7-1.0 for creative tasks, 1.0+ for highly creative output. Most users use 0.7."
            ),
            "max_tokens": ConfigurationParameter(
                name="Max Tokens (Response Length)",
                env_var="AI_MAX_TOKENS",
                description="Maximum number of tokens returned (approximately words/4). Leave empty for unlimited response length. Controls response length and cost. A token is roughly 4 characters or 3/4 of a word.",
                default_value=700,  # Updated based on your feedback
                value_type=int,
                examples=["150", "300", "700", "1500", "3000", ""],
                how_to_choose="Short answers (150-300 tokens), standard responses (500-1000 tokens), detailed content (1500+ tokens). Leave empty for unlimited. Higher values cost more and take longer to generate."
            ),
            "timeout": ConfigurationParameter(
                name="Request Timeout",
                env_var="AI_TIMEOUT",
                description="Maximum time in seconds to wait for a response before giving up. Prevents hanging on slow or failed requests. Leave empty for no timeout limit.",
                default_value=60,
                value_type=int,
                examples=["30", "60", "120", "300", "600", ""],
                how_to_choose="30 seconds for fast models/quick tasks, 60 seconds for standard use, 120+ seconds for complex models or local setups, 600 seconds for very slow models. Leave empty for no timeout limit."
            ),
            "base_url": ConfigurationParameter(
                name="API Base URL (Advanced)",
                env_var="AI_BASE_URL",
                description="The base URL your AI requests are sent to. Leave unset to use the provider's default. Only set this if you route requests through a proxy/gateway or use a self-hosted OpenAI-compatible API. If you're not sure, don't change it.",
                default_value=None,
                value_type=str,
                examples=["", "https://api.openai.com/v1", "http://localhost:11434/v1", "https://your-custom-endpoint.com/v1"],
                how_to_choose="Leave empty for standard cloud providers (OpenAI, Groq, etc.). Use only for local models (Ollama), custom deployments, or when behind a proxy."
            ),
            "text_generation_webui_base_url": ConfigurationParameter(
                name="Text Generation WebUI URL",
                env_var="TEXT_GENERATION_WEBUI_BASE_URL",
                description="URL for Text Generation WebUI (Oobabooga). Automatically set when using local WebUI. Leave empty unless using custom WebUI endpoint.",
                default_value=None,
                value_type=str,
                examples=["", "http://localhost:7860", "http://192.168.1.100:7860"],
                how_to_choose="Leave empty for standard WebUI setup. Use only when WebUI runs on different port or remote machine."
            ),
            "fastchat_base_url": ConfigurationParameter(
                name="FastChat URL",
                env_var="FASTCHAT_BASE_URL",
                description="URL for FastChat server. Automatically set when using FastChat. Leave empty unless using custom FastChat endpoint.",
                default_value=None,
                value_type=str,
                examples=["", "http://localhost:8000", "http://192.168.1.100:8000"],
                how_to_choose="Leave empty for standard FastChat setup. Use only when FastChat runs on different port or remote machine."
            )
        }
    
    def get_parameter(self, param_name: str) -> Optional[ConfigurationParameter]:
        """Get parameter by name"""
        return self.parameters.get(param_name)
    
    def list_parameters(self) -> List[ConfigurationParameter]:
        """Get all available parameters"""
        return list(self.parameters.values())

class ImprovedSetupSystem:
    """Improved setup system addressing user feedback"""
    
    def __init__(self):
        self.os_info = self._detect_os()
        self.provider_registry = AIProviderRegistry()
        self.param_registry = ConfigurationParameterRegistry()
    
    def should_trigger_setup(self) -> bool:
        """Check if setup should be triggered based on environment configuration"""
        # Check for any AI-related environment variables
        ai_env_vars = [
            'AI_API_KEY', 'OPENAI_API_KEY', 'GROQ_API_KEY', 'ANTHROPIC_API_KEY',
            'OPENROUTER_API_KEY', 'TOGETHER_API_KEY'
        ]
        
        has_api_key = any(os.getenv(var) for var in ai_env_vars)
        
        # Check for .env file with AI configuration
        env_file = Path.cwd() / ".env"
        has_env_file = env_file.exists()
        
        # Trigger setup if no API keys and no .env file
        return not has_api_key and not has_env_file
    
    def get_missing_providers(self, selected_provider_ids: List[str]) -> List[str]:
        """Check which selected providers are not installed"""
        missing_providers = []
        
        for provider_id in selected_provider_ids:
            try:
                # Try to import the provider module
                if provider_id == "openai":
                    import openai
                elif provider_id == "anthropic":
                    import anthropic
                elif provider_id == "groq":
                    from groq import Groq
                elif provider_id == "openrouter":
                    import openai  # OpenRouter uses OpenAI client
                elif provider_id == "together":
                    import together
                elif provider_id == "ollama":
                    # Ollama doesn't require a package, just local installation
                    pass
                else:
                    missing_providers.append(provider_id)
            except ImportError:
                missing_providers.append(provider_id)
        
        return missing_providers
    
    def _detect_os(self) -> Dict[str, str]:
        """Detect operating system and return appropriate commands"""
        system = platform.system()
        
        if system == "Windows":
            return {
                "name": "Windows",
                "env_file": Path.home() / ".ai_utilities.env",
                "commands": {
                    "temporary_cmd": "set AI_API_KEY=your-key-here",
                    "temporary_powershell": "$env:AI_API_KEY='your-key-here'",
                    "permanent_powershell": "[Environment]::SetEnvironmentVariable('AI_API_KEY', 'your-key-here', 'User')",
                    "permanent_cmd": 'setx AI_API_KEY "your-key-here"',
                    "reload_powershell": "Restart PowerShell or run: . $PROFILE"
                },
                "shell_options": ["PowerShell", "Command Prompt"]
            }
        else:  # Linux/Mac
            return {
                "name": "Linux/Mac",
                "env_file": Path.home() / ".ai_utilities.env",
                "shell_file": Path.home() / (".zshrc" if "zsh" in os.getenv("SHELL", "") else ".bashrc"),
                "commands": {
                    "temporary": "export AI_API_KEY='your-key-here'",
                    "permanent_zsh": "echo 'export AI_API_KEY=\"your-key-here\"' >> ~/.zshrc",
                    "permanent_bash": "echo 'export AI_API_KEY=\"your-key-here\"' >> ~/.bashrc",
                    "reload": "source ~/.zshrc  # or source ~/.bashrc"
                },
                "shell_options": ["zsh", "bash"]
            }
    
    def _choose_providers_interactive(self) -> List[AIProvider]:
        """Interactive multi-provider selection with space handling"""
        print(self.provider_registry.get_provider_menu())
        
        while True:
            try:
                choice = input(f"\nChoose provider(s) (1-{len(self.provider_registry.providers)} or {len(self.provider_registry.providers) + 1} for all, multiple allowed): ").strip()
                
                # Handle "all" option
                if choice == str(len(self.provider_registry.providers) + 1):
                    return list(self.provider_registry.providers.values())
                
                # Handle multiple selections with space handling
                # Clean up input: remove spaces, handle multiple commas
                cleaned_choice = choice.replace(' ', '').replace(',,', ',')
                selected_indices = [int(x.strip()) - 1 for x in cleaned_choice.split(',') if x.strip()]
                selected_providers = []
                
                for index in selected_indices:
                    if 0 <= index < len(self.provider_registry.providers):
                        provider = list(self.provider_registry.providers.values())[index]
                        selected_providers.append(provider)
                    else:
                        print(f"Invalid number: {index + 1}")
                        raise ValueError
                
                if selected_providers:
                    print(f"\nSelected providers: {', '.join([p.name for p in selected_providers])}")
                    return selected_providers
                else:
                    print("No valid providers selected.")
                    
            except ValueError:
                print("Please enter valid numbers separated by commas (e.g., 1, 3, 5)")
            except Exception as e:
                print(f"Error: {e}")
    
    def _configure_multi_provider_env_vars(self, providers: List[AIProvider]) -> Dict[str, str]:
        """Configure environment variables for multiple providers"""
        print(f"\nConfigure API Keys for {len(providers)} Provider(s)")
        print("=" * 50)
        
        env_vars = {}
        
        for provider in providers:
            print(f"\n{provider.name}")
            print(f"Environment variable: {provider.api_key_env}")
            print(f"Get API key: {provider.setup_url}")
            
            if provider.provider_id == "ollama":
                print("Ollama uses local installation, no API key needed")
                env_vars[provider.api_key_env] = "dummy-key"
            else:
                api_key = getpass.getpass(f"Enter {provider.name} API key (hidden): ").strip()
                if api_key:
                    env_vars[provider.api_key_env] = api_key
                    print(f"{provider.name} API key configured")
                else:
                    print(f"{provider.name} API key skipped")
        
        return env_vars
    
    def _generate_multi_provider_env_file(self, providers: List[AIProvider], env_vars: Dict[str, str], config: Dict[str, any]):
        """Generate .env file for multiple providers"""
        env_file = Path.cwd() / ".env"
        
        with open(env_file, 'w') as f:
            f.write("# AI Utilities Configuration\n")
            f.write("# Multi-Provider Setup\n")
            f.write(f"# Configured providers: {', '.join([p.name for p in providers])}\n\n")
            
            # API keys for all providers
            f.write("# API Keys\n")
            for env_var, value in env_vars.items():
                f.write(f"{env_var}={value}\n")
            
            f.write("\n# Default Configuration\n")
            f.write(f"AI_PROVIDER={config.get('provider', providers[0].provider_id)}\n")
            
            # Common parameters
            for param_name in ["model", "temperature", "max_tokens", "timeout", "base_url", "text_generation_webui_base_url", "fastchat_base_url"]:
                if param_name in config and config[param_name] is not None:
                    param = self.param_registry.get_parameter(param_name)
                    env_var = param.env_var
                    # Handle empty string for max_tokens (unlimited)
                    if param_name == "max_tokens" and config[param_name] == "":
                        f.write(f"# {env_var} is empty for unlimited response length\n")
                    # Handle base_url - write provider default if user left empty
                    elif param_name == "base_url" and config[param_name] == "":
                        # Get the selected provider's default base URL
                        selected_provider = providers[0] if providers else None
                        if selected_provider:
                            f.write(f"{env_var}={selected_provider.base_url_default}\n")
                            f.write(f"# {env_var} set to {selected_provider.name} default\n")
                        else:
                            f.write(f"# {env_var} left empty - no provider selected\n")
                    else:
                        f.write(f"{env_var}={config[param_name]}\n")
        
        # Set secure permissions
        env_file.chmod(0o600)
        
        print(f"✅ Multi-provider configuration saved to {env_file}")
        print(f"🔒 File permissions set to read/write for owner only")
    
    def demonstrate_improvements(self):
        """Demonstrate the improvements made"""
        print("🚀 Improved Setup System - Addressing User Feedback")
        print("=" * 65)
        
        print("\n✅ IMPROVEMENTS MADE:")
        print("1. 💰 Removed specific pricing - now uses cost model descriptions")
        print("2. 🤖 Replaced specific models with model categories")
        print("3. 🎯 Added multi-provider selection support")
        print("4. 🔧 Improved environment variable handling for multiple providers")
        print("5. 📏 Fixed max_tokens default to 700 and improved explanation")
        print("6. 📚 Clarified that tokens = ~1/4 word, not time-based")
        
        print("\n🤖 PROVIDER INFORMATION (Future-Proof):")
        for provider in self.provider_registry.list_providers():
            print(f"\n{provider.name}:")
            print(f"   Cost Model: {provider.cost_model}")
            print(f"   Categories: {', '.join(provider.model_categories)}")
        
        print("\n⚙️ PARAMETER EXPLANATIONS (Accurate):")
        max_tokens = self.param_registry.get_parameter("max_tokens")
        if max_tokens:
            print(f"Max Tokens: {max_tokens.description}")
            print(f"Default: {max_tokens.default_value}")
            print(f"Examples: {', '.join(max_tokens.examples)}")

def main():
    """Demonstrate the improved system"""
    setup = ImprovedSetupSystem()
    setup.demonstrate_improvements()
    
    print("\n🎯 KEY IMPROVEMENTS SUMMARY:")
    print("=" * 40)
    print("✅ Future-proof provider information")
    print("✅ Multi-provider selection capability")
    print("✅ Accurate parameter explanations")
    print("✅ Flexible environment variable handling")
    print("✅ Clear token vs time distinction")

if __name__ == "__main__":
    main()
