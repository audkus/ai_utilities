#!/usr/bin/env python3
"""
Provider Health Monitoring System
Detects changes and issues with AI providers before they affect users.
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass
from dotenv import load_dotenv
from ai_utilities import create_client

@dataclass
class ProviderStatus:
    """Track provider health status."""
    name: str
    endpoint: str
    api_key_env: str
    test_model: str
    last_check: datetime
    status: str  # "healthy", "degraded", "down"
    issues: List[str]
    response_time: float
    changed_since: datetime = None

class ProviderMonitor:
    """Monitor AI provider health and detect changes."""
    
    def __init__(self):
        load_dotenv()
        self.providers = self._setup_providers()
        self.status_file = "provider_health.json"
        self.load_previous_status()
    
    def _setup_providers(self) -> List[Dict]:
        """Configure providers to monitor."""
        return [
            {
                "name": "OpenAI",
                "endpoint": "https://api.openai.com/v1",
                "api_key_env": "AI_API_KEY",
                "test_model": "gpt-3.5-turbo",
                "models_endpoint": "https://api.openai.com/v1/models"
            },
            {
                "name": "Groq",
                "endpoint": "https://api.groq.com/openai/v1",
                "api_key_env": "GROQ_API_KEY",
                "test_model": "llama-3.1-8b-instant",
                "models_endpoint": "https://api.groq.com/openai/v1/models"
            },
            {
                "name": "Together AI",
                "endpoint": "https://api.together.xyz/v1",
                "api_key_env": "TOGETHER_API_KEY",
                "test_model": "meta-llama/Llama-3.2-3B-Instruct-Turbo",
                "models_endpoint": "https://api.together.xyz/v1/models"
            },
            {
                "name": "OpenRouter",
                "endpoint": "https://openrouter.ai/api/v1",
                "api_key_env": "OPENROUTER_API_KEY",
                "test_model": "meta-llama/llama-3.2-3b-instruct:free",
                "models_endpoint": "https://openrouter.ai/api/v1/models"
            },
            {
                "name": "Ollama",
                "endpoint": "http://127.0.0.1:11434/v1",
                "api_key_env": None,
                "test_model": "llama3.2:latest",
                "models_endpoint": "http://127.0.0.1:11434/api/tags"
            },
            {
                "name": "LM Studio",
                "endpoint": "http://127.0.0.1:1234/v1",
                "api_key_env": None,
                "test_model": "local-model",  # Will be updated based on available models
                "models_endpoint": "http://127.0.0.1:1234/v1/models"
            },
            {
                "name": "Text-Generation-WebUI",
                "endpoint": "http://127.0.0.1:5000/v1",
                "api_key_env": "TEXT_GENERATION_WEBUI_API_KEY",
                "test_model": "local-model",  # Will be updated based on available models
                "models_endpoint": "http://127.0.0.1:5000/v1/models"
            },
            {
                "name": "FastChat",
                "endpoint": "http://127.0.0.1:8000/v1",
                "api_key_env": "FASTCHAT_API_KEY",
                "test_model": "vicuna-7b-v1.5",  # Default FastChat model
                "models_endpoint": "http://127.0.0.1:8000/v1/models"
            }
        ]
    
    def load_previous_status(self):
        """Load previous health check results."""
        try:
            with open(self.status_file, 'r') as f:
                data = json.load(f)
                self.previous_status = {
                    name: datetime.fromisoformat(status['last_check'])
                    for name, status in data.items()
                }
        except FileNotFoundError:
            self.previous_status = {}
    
    def save_current_status(self, results: Dict[str, ProviderStatus]):
        """Save current health check results."""
        data = {}
        for name, status in results.items():
            data[name] = {
                "last_check": status.last_check.isoformat(),
                "status": status.status,
                "issues": status.issues,
                "response_time": status.response_time
            }
        
        with open(self.status_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def check_provider_health(self, provider: Dict) -> ProviderStatus:
        """Comprehensive health check for a provider."""
        start_time = datetime.now()
        issues = []
        
        # Check 1: API Key
        api_key = os.getenv(provider["api_key_env"]) if provider["api_key_env"] else "dummy-key"
        if not api_key and provider["api_key_env"]:
            issues.append("API key not found")
        
        # Check 2: Endpoint Reachability
        try:
            # Add API key to headers for cloud providers
            headers = {}
            if provider["api_key_env"] and api_key != "dummy-key":
                headers["Authorization"] = f"Bearer {api_key}"
            
            response = requests.get(provider["models_endpoint"], headers=headers, timeout=5)
            if response.status_code == 200:
                # Check 3: Model Availability
                if provider["name"] in ["Ollama"]:
                    models_data = response.json()
                    available_models = [m["name"] for m in models_data.get("models", [])]
                elif provider["name"] in ["Together AI", "Text-Generation-WebUI", "FastChat"]:
                    # Together AI, Text-Generation-WebUI, and FastChat return a list directly
                    models_data = response.json()
                    available_models = [m["id"] for m in models_data]
                else:
                    models_data = response.json()
                    available_models = [m["id"] for m in models_data.get("data", [])]
                
                if provider["test_model"] not in available_models:
                    issues.append(f"Test model {provider['test_model']} not available")
                    # Find alternative model
                    if available_models:
                        provider["test_model"] = available_models[0]
                        issues.append(f"Using alternative model: {available_models[0]}")
            else:
                issues.append(f"Models endpoint returned {response.status_code}")
        except Exception as e:
            issues.append(f"Endpoint unreachable: {str(e)}")
        
        # Check 4: Actual API Call
        try:
            if provider["name"] in ["Ollama", "LM Studio"]:
                client = create_client(
                    provider="openai_compatible",
                    base_url=provider["endpoint"],
                    model=provider["test_model"],
                    api_key="dummy-key",
                    show_progress=False
                )
            else:
                client = create_client(
                    provider="openai_compatible",
                    base_url=provider["endpoint"],
                    api_key=api_key,
                    model=provider["test_model"],
                    show_progress=False
                )
            
            response = client.ask("Health check", max_tokens=3, temperature=0.1)
            if not response or len(response.strip()) == 0:
                issues.append("Empty response from API")
            
        except Exception as e:
            issues.append(f"API call failed: {str(e)}")
        
        # Determine status
        response_time = (datetime.now() - start_time).total_seconds()
        if not issues:
            status = "healthy"
        elif len(issues) <= 2 and "rate limit" not in str(issues).lower():
            status = "degraded"
        else:
            status = "down"
        
        return ProviderStatus(
            name=provider["name"],
            endpoint=provider["endpoint"],
            api_key_env=provider["api_key_env"],
            test_model=provider["test_model"],
            last_check=start_time,
            status=status,
            issues=issues,
            response_time=response_time
        )
    
    def detect_changes(self, results: Dict[str, ProviderStatus]):
        """Detect changes in provider status."""
        changes = []
        
        for name, status in results.items():
            if name in self.previous_status:
                time_since_last = datetime.now() - self.previous_status[name]
                if time_since_last > timedelta(hours=24):
                    changes.append(f"{name}: Not checked in {time_since_last.days} days")
            
            if status.status != "healthy":
                changes.append(f"{name}: {status.status.upper()} - {', '.join(status.issues)}")
            
            if status.response_time > 10.0:
                changes.append(f"{name}: Slow response ({status.response_time:.1f}s)")
        
        return changes
    
    def run_health_check(self):
        """Run comprehensive health check."""
        print("🏥 PROVIDER HEALTH MONITOR")
        print("=" * 50)
        
        results = {}
        
        for provider in self.providers:
            print(f"\n🔍 Checking {provider['name']}...")
            status = self.check_provider_health(provider)
            results[provider['name']] = status
            
            # Display results
            status_icon = {"healthy": "✅", "degraded": "⚠️", "down": "❌"}[status.status]
            print(f"   {status_icon} Status: {status.status.upper()}")
            print(f"   ⏱️  Response time: {status.response_time:.2f}s")
            print(f"   🤖 Model: {status.test_model}")
            
            if status.issues:
                for issue in status.issues:
                    print(f"   ⚠️  {issue}")
        
        # Detect changes
        changes = self.detect_changes(results)
        
        if changes:
            print("\n🚨 CHANGES DETECTED:")
            for change in changes:
                print(f"   • {change}")
        else:
            print("\n✅ No significant changes detected")
        
        # Save results
        self.save_current_status(results)
        
        # Summary
        healthy = sum(1 for s in results.values() if s.status == "healthy")
        total = len(results)
        print(f"\n📊 SUMMARY: {healthy}/{total} providers healthy")
        
        return results

def main():
    """Run the provider health monitor."""
    monitor = ProviderMonitor()
    results = monitor.run_health_check()
    
    print("\n💡 RECOMMENDATIONS:")
    print("• Run this monitor daily to detect issues early")
    print("• Set up automated alerts for status changes")
    print("• Keep fallback providers ready for critical applications")
    print("• Update test models when providers add/remove models")

if __name__ == "__main__":
    main()
