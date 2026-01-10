#!/usr/bin/env python3
"""
Enhanced AI Utilities Setup System
Phase 2: OS-Specific Instructions + Interactive Setup
Phase 3: Enhanced Security + Multi-Provider Configuration
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
    """AI Provider configuration with user-friendly descriptions"""
    name: str
    provider_id: str
    description: str
    api_key_env: str
    base_url_default: str
    models: List[str]
    setup_url: str
    pricing_info: str
    requires_extra_install: bool = True
    
    def get_user_friendly_info(self) -> str:
        """Return formatted provider information for users"""
        return f"""
🤖 {self.name}
   {self.description}
   
📍 API Key Environment: {self.api_key_env}
🔗 Get API Key: {self.setup_url}
💰 Pricing: {self.pricing_info}
🚀 Popular Models: {', '.join(self.models[:3])}{'...' if len(self.models) > 3 else ''}

⚙️  Installation: pip install "ai-utilities[{self.provider_id}]"
        """

class AIProviderRegistry:
    """Registry of supported AI providers with detailed information"""
    
    def __init__(self):
        self.providers = {
            "openai": AIProvider(
                name="OpenAI",
                provider_id="openai",
                description="Most popular AI provider with GPT models, excellent for general tasks, coding, and creative writing.",
                api_key_env="OPENAI_API_KEY",
                base_url_default="https://api.openai.com/v1",
                models=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                setup_url="https://platform.openai.com/api-keys",
                pricing_info="$0.03-0.06 per 1K tokens (GPT-4), $0.001-0.002 per 1K tokens (GPT-3.5)",
                requires_extra_install=True
            ),
            "groq": AIProvider(
                name="Groq",
                provider_id="groq",
                description="Ultra-fast inference speeds, perfect for real-time applications and high-throughput use cases.",
                api_key_env="GROQ_API_KEY",
                base_url_default="https://api.groq.com/openai/v1",
                models=["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
                setup_url="https://console.groq.com/keys",
                pricing_info="Free tier available, then $0.19-0.89 per 1M tokens",
                requires_extra_install=False
            ),
            "together": AIProvider(
                name="Together AI",
                provider_id="together",
                description="Wide variety of open-source models, cost-effective for specialized tasks and experimentation.",
                api_key_env="TOGETHER_API_KEY",
                base_url_default="https://api.together.xyz/v1",
                models=["meta-llama/Llama-3.2-3B-Instruct-Turbo", "Qwen/Qwen2.5-7B-Instruct-Turbo"],
                setup_url="https://api.together.xyz/settings/api-keys",
                pricing_info="$0.18-2.50 per 1M tokens depending on model",
                requires_extra_install=False
            ),
            "anthropic": AIProvider(
                name="Anthropic Claude",
                provider_id="anthropic",
                description="Advanced reasoning and safety features, excellent for complex analytical tasks.",
                api_key_env="ANTHROPIC_API_KEY",
                base_url_default="https://api.anthropic.com",
                models=["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
                setup_url="https://console.anthropic.com/",
                pricing_info="$3-15 per 1M tokens depending on model",
                requires_extra_install=False
            ),
            "openrouter": AIProvider(
                name="OpenRouter",
                provider_id="openrouter",
                description="Access to multiple models through a single API, great for comparing model performance.",
                api_key_env="OPENROUTER_API_KEY",
                base_url_default="https://openrouter.ai/api/v1",
                models=["anthropic/claude-3.5-sonnet", "openai/gpt-4o", "meta-llama/llama-3.1-70b-instruct"],
                setup_url="https://openrouter.ai/keys",
                pricing_info="Varies by model, typically $0.10-15 per 1M tokens",
                requires_extra_install=False
            ),
            "ollama": AIProvider(
                name="Ollama (Local)",
                provider_id="ollama",
                description="Run models locally on your own machine, complete privacy, no API costs.",
                api_key_env="dummy-key",
                base_url_default="http://localhost:11434/v1",
                models=["llama3.2:latest", "qwen2.5:latest", "codellama:latest"],
                setup_url="https://ollama.com/download",
                pricing_info="Free (runs on your hardware)",
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
        """Generate a formatted menu of providers"""
        menu = "\n🤖 Available AI Providers:\n"
        menu += "=" * 50 + "\n"
        
        for i, (provider_id, provider) in enumerate(self.providers.items(), 1):
            menu += f"\n{i}. {provider.name} ({provider_id})"
            menu += f"\n   {provider.description[:80]}{'...' if len(provider.description) > 80 else ''}"
            menu += f"\n   💰 {provider.pricing_info}"
        
        menu += "\n" + "=" * 50
        return menu

@dataclass
class ConfigurationParameter:
    """Configuration parameter with user-friendly explanation"""
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
⚙️  {self.name}
   {self.description}
   
📝 Environment Variable: {self.env_var}
🎯 Default: {self.default_value}
📋 Examples: {', '.join(self.examples)}
💡 How to choose: {self.how_to_choose}

Enter value (or press Enter for default {self.default_value}): """

class ConfigurationParameterRegistry:
    """Registry of configuration parameters with detailed explanations"""
    
    def __init__(self):
        self.parameters = {
            "model": ConfigurationParameter(
                name="AI Model",
                env_var="AI_MODEL",
                description="The specific AI model to use for generating responses. Different models have different capabilities, speeds, and costs.",
                default_value="gpt-3.5-turbo",
                value_type=str,
                examples=["gpt-4", "gpt-3.5-turbo", "claude-3-5-sonnet", "llama3.2:latest"],
                how_to_choose="Choose based on your needs: GPT-4 for complex tasks, GPT-3.5 for speed/cost efficiency, local models for privacy."
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
                description="Maximum number of tokens (words/sub-words) the AI can generate in a response. Controls response length and cost.",
                default_value=1000,
                value_type=int,
                examples=["100", "500", "1000", "2000", "4000"],
                how_to_choose="Short answers (100-300), detailed responses (500-1000), long content (1500-4000). Higher values cost more and take longer."
            ),
            "timeout": ConfigurationParameter(
                name="Request Timeout",
                env_var="AI_TIMEOUT",
                description="Maximum time to wait for a response before giving up. Prevents hanging on slow or failed requests.",
                default_value=60,
                value_type=int,
                examples=["30", "60", "120", "300"],
                how_to_choose="30 seconds for fast models/quick tasks, 60 seconds standard, 120+ seconds for complex models or slow networks."
            ),
            "base_url": ConfigurationParameter(
                name="API Base URL",
                env_var="AI_BASE_URL",
                description="Custom API endpoint URL. Only needed for custom deployments, proxies, or alternative endpoints.",
                default_value=None,
                value_type=str,
                examples=["https://api.openai.com/v1", "https://api.groq.com/openai/v1", "http://localhost:11434/v1"],
                how_to_choose="Use default unless using custom deployment, proxy, or local server. Most users never need to change this."
            )
        }
    
    def get_parameter(self, param_name: str) -> Optional[ConfigurationParameter]:
        """Get parameter by name"""
        return self.parameters.get(param_name)
    
    def list_parameters(self) -> List[ConfigurationParameter]:
        """Get all available parameters"""
        return list(self.parameters.values())

class EnhancedSetupSystem:
    """Enhanced setup system with OS detection, multi-provider support, and detailed guidance"""
    
    def __init__(self):
        self.os_info = self._detect_os()
        self.provider_registry = AIProviderRegistry()
        self.param_registry = ConfigurationParameterRegistry()
    
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
    
    def run_enhanced_setup(self) -> Dict[str, any]:
        """Run the complete enhanced setup process"""
        print("🚀 AI Utilities Enhanced Setup")
        print("=" * 60)
        print(f"🖥️  Detected OS: {self.os_info['name']}")
        print()
        
        # Step 1: Choose setup method
        method = self._choose_setup_method()
        
        if method == "interactive":
            return self._run_interactive_setup()
        elif method == "guided":
            return self._run_guided_setup()
        elif method == "manual":
            return self._show_manual_instructions()
        else:
            print("❌ Invalid choice. Please try again.")
            return self.run_enhanced_setup()
    
    def _choose_setup_method(self) -> str:
        """Let user choose setup method"""
        print("🎯 How would you like to set up AI Utilities?")
        print()
        print("1. 🤖 Interactive Setup - Answer questions, I'll configure everything")
        print("2. 📋 Guided Setup - Step-by-step instructions with choices")
        print("3. 📖 Manual Instructions - Show me all options and commands")
        print()
        
        choice = input("Choose option (1-3): ").strip()
        
        if choice == "1":
            return "interactive"
        elif choice == "2":
            return "guided"
        elif choice == "3":
            return "manual"
        else:
            print("❌ Please enter 1, 2, or 3.")
            return self._choose_setup_method()
    
    def _run_interactive_setup(self) -> Dict[str, any]:
        """Run fully interactive setup"""
        print("\n🤖 Interactive Setup - I'll guide you through everything")
        print("=" * 60)
        
        config = {}
        
        # Step 1: Choose primary provider
        provider = self._choose_provider_interactive()
        config["provider"] = provider.provider_id
        config["provider_info"] = provider
        
        # Step 2: Configure API key
        api_key = self._setup_api_key_interactive(provider)
        config["api_key"] = api_key
        
        # Step 3: Configure parameters
        config.update(self._configure_parameters_interactive())
        
        # Step 4: Save configuration
        self._save_configuration(config)
        
        return config
    
    def _choose_provider_interactive(self) -> AIProvider:
        """Interactive provider selection"""
        print(self.provider_registry.get_provider_menu())
        
        while True:
            try:
                choice = input(f"\nChoose provider (1-{len(self.provider_registry.providers)}): ").strip()
                provider_index = int(choice) - 1
                
                if 0 <= provider_index < len(self.provider_registry.providers):
                    provider = list(self.provider_registry.providers.values())[provider_index]
                    print(f"\n✅ Selected: {provider.name}")
                    print(provider.get_user_friendly_info())
                    
                    confirm = input("\nConfirm this provider? (Y/n): ").strip().lower()
                    if confirm in ['', 'y', 'yes']:
                        return provider
                else:
                    print("❌ Invalid number. Please try again.")
            except ValueError:
                print("❌ Please enter a number.")
    
    def _setup_api_key_interactive(self, provider: AIProvider) -> str:
        """Interactive API key setup"""
        print(f"\n🔑 Setting up API key for {provider.name}")
        print("-" * 40)
        
        print(f"📍 You'll need an API key from: {provider.setup_url}")
        print(f"🔍 It should be set as: {provider.api_key_env}")
        
        if input("Have you copied your API key? (Y/n): ").strip().lower() in ['', 'y', 'yes']:
            api_key = getpass.getpass("Paste your API key (hidden input): ").strip()
            
            if not api_key:
                print("❌ No API key provided.")
                return self._setup_api_key_interactive(provider)
            
            # Basic validation
            if len(api_key) < 10:
                print("⚠️  This seems too short for an API key. Please check.")
                if input("Continue anyway? (y/N): ").strip().lower() != 'y':
                    return self._setup_api_key_interactive(provider)
            
            print(f"✅ API key configured for {provider.name}")
            return api_key
        else:
            print("⏸️  Skipping API key setup. You can configure it later.")
            return ""
    
    def _configure_parameters_interactive(self) -> Dict[str, any]:
        """Interactive parameter configuration"""
        print(f"\n⚙️  Configure AI Parameters")
        print("-" * 30)
        print("💡 You can press Enter to accept defaults for any parameter")
        print()
        
        config = {}
        
        for param in self.param_registry.list_parameters():
            print(param.get_user_prompt())
            
            user_input = input().strip()
            
            if user_input:
                try:
                    if param.value_type == int:
                        value = int(user_input)
                    elif param.value_type == float:
                        value = float(user_input)
                    else:
                        value = user_input
                    
                    config[param.name] = value
                    print(f"✅ Set {param.name} = {value}")
                except ValueError:
                    print(f"❌ Invalid {param.name}. Using default: {param.default_value}")
                    config[param.name] = param.default_value
            else:
                config[param.name] = param.default_value
                print(f"✅ Using default {param.name}: {param.default_value}")
            
            print()
        
        return config
    
    def _save_configuration(self, config: Dict[str, any]):
        """Save configuration to .env file"""
        print("💾 Saving configuration...")
        
        env_file = Path.cwd() / ".env"
        
        # Check if file exists
        if env_file.exists():
            print(f"⚠️  {env_file} already exists.")
            overwrite = input("Overwrite? (y/N): ").strip().lower()
            if overwrite != 'y':
                print("❌ Configuration not saved.")
                return
        
        # Write configuration
        with open(env_file, 'w') as f:
            f.write("# AI Utilities Configuration\n")
            f.write("# Generated by Enhanced Setup System\n")
            f.write(f"# Provider: {config['provider_info'].name}\n\n")
            
            # API key
            if config.get("api_key"):
                f.write(f"AI_API_KEY={config['api_key']}\n")
                f.write(f"{config['provider_info'].api_key_env}={config['api_key']}\n\n")
            
            # Provider
            f.write(f"AI_PROVIDER={config['provider']}\n")
            
            # Parameters
            for param_name in ["model", "temperature", "max_tokens", "timeout", "base_url"]:
                if param_name in config and config[param_name] is not None:
                    env_var = self.param_registry.get_parameter(param_name).env_var
                    f.write(f"{env_var}={config[param_name]}\n")
        
        # Set secure permissions
        env_file.chmod(0o600)
        
        print(f"✅ Configuration saved to {env_file}")
        print(f"🔒 File permissions set to read/write for owner only")
        print(f"🚀 You can now use AI Utilities!")
    
    def _run_guided_setup(self) -> Dict[str, any]:
        """Run guided setup with step-by-step instructions"""
        print("\n📋 Guided Setup - Step-by-step instructions")
        print("=" * 50)
        
        # This would provide step-by-step guidance
        # For now, delegate to interactive
        return self._run_interactive_setup()
    
    def _show_manual_instructions(self) -> Dict[str, any]:
        """Show comprehensive manual instructions"""
        print(f"\n📖 Manual Setup Instructions for {self.os_info['name']}")
        print("=" * 60)
        
        # OS-specific environment variable instructions
        print("\n🔧 Environment Variable Setup:")
        print("-" * 30)
        
        if self.os_info["name"] == "Windows":
            print("PowerShell (Recommended):")
            print(f"  $env:AI_API_KEY='your-key-here'")
            print(f"  {self.os_info['commands']['permanent_powershell']}")
            print(f"  {self.os_info['commands']['reload_powershell']}")
            
            print("\nCommand Prompt:")
            print(f"  {self.os_info['commands']['temporary_cmd']}")
            print(f"  {self.os_info['commands']['permanent_cmd']}")
        else:
            print("Temporary (current session):")
            print(f"  {self.os_info['commands']['temporary']}")
            
            print("\nPermanent (add to shell):")
            print(f"  {self.os_info['commands']['permanent_zsh']}")
            print(f"  {self.os_info['commands']['reload']}")
        
        # Provider information
        print("\n🤖 Supported Providers:")
        print("-" * 25)
        for provider in self.provider_registry.list_providers():
            print(f"\n{provider.name}:")
            print(f"  API Key: {provider.api_key_env}")
            print(f"  Setup: {provider.setup_url}")
        
        # Configuration parameters
        print("\n⚙️  Configuration Parameters:")
        print("-" * 30)
        for param in self.param_registry.list_parameters():
            print(f"\n{param.name} ({param.env_var}):")
            print(f"  {param.description}")
            print(f"  Default: {param.default_value}")
        
        return {}

# Main execution
if __name__ == "__main__":
    setup = EnhancedSetupSystem()
    config = setup.run_enhanced_setup()
    
    if config:
        print("\n🎉 Setup completed successfully!")
        print("You can now use AI Utilities with your configuration.")
    else:
        print("\n📖 Setup instructions displayed. Follow them to configure AI Utilities.")
