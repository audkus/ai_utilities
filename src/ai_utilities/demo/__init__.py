"""
Demo module for model discovery and validation tests.

This module provides demo functionality for testing model discovery,
validation, and provider capabilities without requiring actual API calls.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class DemoModel:
    """Demo model information for testing."""
    id: str
    name: str
    provider: str
    capabilities: List[str]
    context_length: Optional[int] = None
    pricing: Optional[Dict[str, float]] = None

class DemoModelDiscovery:
    """Demo model discovery service for testing."""
    
    def __init__(self):
        self._demo_models = {
            "openai": [
                DemoModel(
                    id="gpt-4o",
                    name="GPT-4o",
                    provider="openai",
                    capabilities=["text", "json", "function_calling", "vision"],
                    context_length=128000,
                    pricing={"prompt": 0.005, "completion": 0.015}
                ),
                DemoModel(
                    id="gpt-4o-mini",
                    name="GPT-4o Mini", 
                    provider="openai",
                    capabilities=["text", "json", "function_calling"],
                    context_length=128000,
                    pricing={"prompt": 0.00015, "completion": 0.0006}
                ),
                DemoModel(
                    id="gpt-3.5-turbo",
                    name="GPT-3.5 Turbo",
                    provider="openai", 
                    capabilities=["text", "json", "function_calling"],
                    context_length=16384,
                    pricing={"prompt": 0.0005, "completion": 0.0015}
                )
            ],
            "groq": [
                DemoModel(
                    id="llama3-70b-8192",
                    name="Llama 3 70B",
                    provider="groq",
                    capabilities=["text", "json"],
                    context_length=8192,
                    pricing={"prompt": 0.00059, "completion": 0.00079}
                ),
                DemoModel(
                    id="mixtral-8x7b-32768",
                    name="Mixtral 8x7B",
                    provider="groq",
                    capabilities=["text", "json"],
                    context_length=32768,
                    pricing={"prompt": 0.00024, "completion": 0.00024}
                )
            ],
            "together": [
                DemoModel(
                    id="meta-llama/Llama-3-8b-chat-hf",
                    name="Llama 3 8B Chat",
                    provider="together",
                    capabilities=["text", "json"],
                    context_length=8192,
                    pricing={"prompt": 0.00018, "completion": 0.00018}
                ),
                DemoModel(
                    id="mistralai/Mixtral-8x7B-Instruct-v0.1",
                    name="Mixtral 8x7B Instruct",
                    provider="together", 
                    capabilities=["text", "json"],
                    context_length=32768,
                    pricing={"prompt": 0.00030, "completion": 0.00030}
                )
            ],
            "openrouter": [
                DemoModel(
                    id="meta-llama/llama-3-8b-instruct:free",
                    name="Llama 3 8B Instruct (Free)",
                    provider="openrouter",
                    capabilities=["text", "json"],
                    context_length=8192,
                    pricing={"prompt": 0.0, "completion": 0.0}
                ),
                DemoModel(
                    id="anthropic/claude-3-haiku:beta",
                    name="Claude 3 Haiku",
                    provider="openrouter",
                    capabilities=["text", "json"],
                    context_length=200000,
                    pricing={"prompt": 0.00025, "completion": 0.000125}
                )
            ],
            "ollama": [
                DemoModel(
                    id="llama3.1",
                    name="Llama 3.1",
                    provider="ollama",
                    capabilities=["text"],
                    context_length=131072
                ),
                DemoModel(
                    id="codellama",
                    name="Code Llama",
                    provider="ollama",
                    capabilities=["text", "code"],
                    context_length=16384
                )
            ],
            "lmstudio": [
                DemoModel(
                    id="lm-studio-test",
                    name="LM Studio Test Model",
                    provider="lmstudio",
                    capabilities=["text"],
                    context_length=4096
                )
            ],
            "text-generation-webui": [
                DemoModel(
                    id="webui-test",
                    name="WebUI Test Model",
                    provider="text-generation-webui",
                    capabilities=["text"],
                    context_length=2048
                )
            ],
            "fastchat": [
                DemoModel(
                    id="fastchat-test",
                    name="FastChat Test Model",
                    provider="fastchat", 
                    capabilities=["text"],
                    context_length=4096
                )
            ]
        }
    
    def discover_models(self, provider: str) -> List[DemoModel]:
        """Discover models for a specific provider."""
        return self._demo_models.get(provider, [])
    
    def get_all_models(self) -> Dict[str, List[DemoModel]]:
        """Get all demo models by provider."""
        return self._demo_models
    
    def get_model(self, provider: str, model_id: str) -> Optional[DemoModel]:
        """Get a specific model by provider and ID."""
        models = self._demo_models.get(provider, [])
        for model in models:
            if model.id == model_id:
                return model
        return None

class DemoValidator:
    """Demo validator for testing model validation functionality."""
    
    def __init__(self):
        self.discovery = DemoModelDiscovery()
    
    def validate_model(self, provider: str, model_id: str) -> Dict[str, Any]:
        """Validate a model and return validation results."""
        model = self.discovery.get_model(provider, model_id)
        
        if not model:
            return {
                "valid": False,
                "error": f"Model {model_id} not found for provider {provider}",
                "provider": provider,
                "model_id": model_id
            }
        
        # Demo validation checks
        validation_results = {
            "valid": True,
            "provider": provider,
            "model_id": model_id,
            "model_name": model.name,
            "checks": {
                "model_exists": True,
                "capabilities_supported": True,
                "context_length_valid": model.context_length is not None and model.context_length > 0,
                "pricing_available": model.pricing is not None
            },
            "capabilities": model.capabilities,
            "context_length": model.context_length,
            "pricing": model.pricing
        }
        
        return validation_results
    
    def validate_provider(self, provider: str) -> Dict[str, Any]:
        """Validate a provider and return validation results."""
        models = self.discovery.discover_models(provider)
        
        if not models:
            return {
                "valid": False,
                "error": f"No models found for provider {provider}",
                "provider": provider,
                "model_count": 0
            }
        
        validation_results = {
            "valid": True,
            "provider": provider,
            "model_count": len(models),
            "models": [{"id": m.id, "name": m.name} for m in models],
            "checks": {
                "has_models": len(models) > 0,
                "models_have_capabilities": all(m.capabilities for m in models),
                "models_have_context": all(m.context_length for m in models)
            }
        }
        
        return validation_results

# Global instances for easy access
demo_discovery = DemoModelDiscovery()
demo_validator = DemoValidator()

def get_demo_models(provider: str) -> List[DemoModel]:
    """Get demo models for a provider."""
    return demo_discovery.discover_models(provider)

def validate_demo_model(provider: str, model_id: str) -> Dict[str, Any]:
    """Validate a demo model."""
    return demo_validator.validate_model(provider, model_id)
