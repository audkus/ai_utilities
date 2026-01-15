#!/usr/bin/env python3
"""
Text-Generation-WebUI API Detection and Setup Helper
Helps find and configure the API endpoint.
"""

import requests
import subprocess
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class WebUIAPIHelper:
    """Helper class for detecting and configuring WebUI APIs."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize WebUI API helper.
        
        Args:
            config_file: Optional path to configuration file
        """
        self.config_file = config_file
        
        # Load configuration from file if provided
        if config_file and Path(config_file).exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                # Extract webui configurations
                webuis = config.get("webuis", {})
                self.supported_webuis = list(webuis.keys())
                self.default_ports = {name: info.get("default_port", 7860) for name, info in webuis.items()}
                self.health_endpoints = {name: info.get("health_endpoint", "/") for name, info in webuis.items()}
                self.config_templates = {
                    name: {
                        "provider": info.get("api_format", "openai_compatible"),
                        "base_url": f"http://localhost:{info.get('default_port', 7860)}",
                        "api_key": "sk-123456"
                    } for name, info in webuis.items()
                }
        else:
            # Default configuration
            self.supported_webuis = ["text-generation-webui", "fastchat"]
            self.default_ports = {
                "text-generation-webui": 7860,
                "fastchat": 8000
            }
            self.health_endpoints = {
                "text-generation-webui": "/",
                "fastchat": "/v1/models"
            }
            self.config_templates = {
                "text-generation-webui": {
                    "provider": "openai_compatible",
                    "base_url": "http://localhost:7860",
                    "api_key": "sk-123456"
                },
                "fastchat": {
                    "provider": "openai_compatible", 
                    "base_url": "http://localhost:8000/v1",
                    "api_key": "sk-123456"
                }
            }
    
    def detect_webui_on_port(self, port: int) -> Dict[str, Any]:
        """Detect if a WebUI is running on the specified port."""
        import time
        start_time = time.time()
        
        try:
            response = requests.get(f"http://127.0.0.1:{port}", timeout=5)
            response_time_ms = max(1, int((time.time() - start_time) * 1000))
            
            if response.status_code == 200:
                # Try to identify the WebUI type
                webui_type = self.identify_webui_type(f"http://127.0.0.1:{port}")
                if not webui_type:
                    webui_type = "unknown"
                
                return {
                    "detected": True,
                    "webui_type": webui_type,
                    "port": port,
                    "endpoint": f"http://127.0.0.1:{port}",
                    "status": "running",
                    "url": f"http://127.0.0.1:{port}",
                    "response_time_ms": response_time_ms
                }
        except:
            pass
        
        response_time_ms = max(1, int((time.time() - start_time) * 1000))
        return {
            "detected": False,
            "webui_type": "unknown",
            "port": port,
            "endpoint": f"http://127.0.0.1:{port}",
            "status": "not_running",
            "url": f"http://127.0.0.1:{port}",
            "response_time_ms": response_time_ms
        }
    
    def scan_for_webuis(self, ports: List[int]) -> List[Dict[str, Any]]:
        """Scan for WebUIs on multiple ports."""
        results = []
        for port in ports:
            result = self.detect_webui_on_port(port)
            if result and result.get("detected", False):
                results.append(result)
        return results
    
    def identify_webui_type(self, url: str) -> Optional[str]:
        """Identify the type of WebUI at the given URL."""
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return "text-generation-webui"
        except:
            pass
        return None
    
    def generate_ai_utilities_config(self, webui_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate ai-utilities configuration for detected WebUI."""
        webui_type = webui_info.get("type", "text-generation-webui")
        port = webui_info.get("port", 7860)
        
        base_config = self.config_templates.get(webui_type, self.config_templates["text-generation-webui"])
        config = base_config.copy()
        config["base_url"] = f"http://localhost:{port}"
        
        return config
    
    def generate_env_file_content(self, webui_info: Dict[str, Any]) -> str:
        """Generate .env file content for WebUI configuration."""
        config = self.generate_ai_utilities_config(webui_info)
        
        env_lines = [
            f"AI_UTILITIES_PROVIDER={config['provider']}",
            f"AI_UTILITIES_BASE_URL={config['base_url']}",
            f"AI_UTILITIES_API_KEY={config['api_key']}"
        ]
        
        return "\n".join(env_lines)
    
    def auto_detect_and_configure(self) -> Optional[Dict[str, Any]]:
        """Auto-detect WebUI and return configuration."""
        for webui_type, port in self.default_ports.items():
            result = self.detect_webui_on_port(port)
            if result:
                result["type"] = webui_type
                return self.generate_ai_utilities_config(result)
        return None
    
    def test_webui_connection(self, config: Dict[str, Any]) -> bool:
        """Test connection to WebUI using the provided configuration."""
        try:
            base_url = config.get("base_url", "http://localhost:7860")
            response = requests.get(base_url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def save_config_json(self, config: Dict[str, Any], output_file: Path) -> None:
        """Save configuration to JSON file."""
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def save_config_env(self, config: Dict[str, Any], env_file: str) -> None:
        """Save configuration to .env file."""
        env_content = self.generate_env_file_content({"type": "text-generation-webui", "config": config})
        with open(env_file, 'w') as f:
            f.write(env_content)
    
    def run_discovery_process(self, output_file: str) -> Optional[Dict[str, Any]]:
        """Run the complete discovery process and save configuration."""
        config = self.auto_detect_and_configure()
        if config:
            self.save_config_json(config, Path(output_file))
        return config
    
    def get_supported_webuis(self) -> Dict[str, Any]:
        """Get information about supported WebUIs."""
        return {
            "supported": self.supported_webuis,
            "default_ports": self.default_ports,
            "health_endpoints": self.health_endpoints
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate WebUI configuration."""
        required_fields = ["provider", "base_url", "api_key"]
        return all(field in config for field in required_fields)
    
    def run_continuous_monitoring(self, interval: float = 5.0, duration: float = 60.0) -> List[Dict[str, Any]]:
        """Run continuous monitoring for WebUIs."""
        import time
        results = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            for port in self.default_ports.values():
                result = self.detect_webui_on_port(port)
                if result:
                    results.append(result)
            time.sleep(interval)
        
        return results
    
    def get_status_summary(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary of scan results."""
        return {
            "total_found": len(scan_results),
            "webuis": [result["type"] for result in scan_results],
            "ports": [result["port"] for result in scan_results]
        }


def check_webui_status():
    """Check if Text-Generation-WebUI web interface is running."""
    try:
        response = requests.get("http://127.0.0.1:7860", timeout=5)
        if response.status_code == 200:
            print("✅ Text-Generation-WebUI web interface is running on port 7860")
            return True
    except:
        pass
    print("❌ Text-Generation-WebUI web interface not found on port 7860")
    return False

def find_api_port():
    """Search for the API port."""
    common_ports = [5000, 5001, 5002, 5003, 8000, 8001, 8080, 8890]
    
    print("🔍 Searching for Text-Generation-WebUI API...")
    
    for port in common_ports:
        try:
            response = requests.get(f"http://127.0.0.1:{port}/v1/models", timeout=2)
            if response.status_code == 200:
                print(f"✅ Found API on port {port}")
                return port
        except:
            continue
    
    print("❌ API not found on common ports")
    return None

def test_api_connection(port):
    """Test the API connection and get model info."""
    try:
        response = requests.get(f"http://127.0.0.1:{port}/v1/models", timeout=5)
        if response.status_code == 200:
            models_data = response.json()
            
            if isinstance(models_data, dict) and "data" in models_data:
                models = models_data["data"]
            elif isinstance(models_data, list):
                models = models_data
            else:
                print("❌ Unexpected response format")
                return False
            
            print(f"✅ API is working! Found {len(models)} models:")
            for i, model in enumerate(models[:5]):  # Show first 5
                model_id = model.get("id", "Unknown")
                print(f"   {i+1}. {model_id}")
            
            if len(models) > 5:
                print(f"   ... and {len(models) - 5} more")
            
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

def main():
    print("🤖 Text-Generation-WebUI API Detection Helper")
    print("=" * 60)
    
    # Check web interface
    if not check_webui_status():
        print("\n💡 To start Text-Generation-WebUI:")
        print("   cd /path/to/text-generation-webui")
        print("   python server.py")
        print("   Then open http://127.0.0.1:7860 in your browser")
        return
    
    # Find API port
    api_port = find_api_port()
    
    if not api_port:
        print("\n❌ API not found. The API server may not be started.")
        print("\n💡 To start the API server:")
        print("   cd /path/to/text-generation-webui")
        print("   python server.py --api --listen")
        print("   # If port 5000 is busy, use:")
        print("   python server.py --api --listen --api-port 5001")
        print("\n🔄 After starting the API, run this script again.")
        return
    
    # Test API connection
    print(f"\n🧪 Testing API connection on port {api_port}...")
    if test_api_connection(api_port):
        print(f"\n🎉 SUCCESS! Text-Generation-WebUI API is working!")
        print(f"\n📝 Configuration for AI Utilities:")
        print(f"   # Add to your .env file:")
        print(f"   TEXT_GENERATION_WEBUI_BASE_URL=http://127.0.0.1:{api_port}/v1")
        print(f"   # TEXT_GENERATION_WEBUI_API_KEY=your-key-here  # Optional")
        
        print(f"\n🚀 Test with AI Utilities:")
        print(f"   python tests/provider_monitoring/test_text_generation_webui.py")
        
        print(f"\n💻 Usage example:")
        print(f"   from ai_utilities import create_client")
        print(f"   client = create_client(")
        print(f"       provider='openai_compatible',")
        print(f"       base_url='http://127.0.0.1:{api_port}/v1',")
        print(f"       model='your-model-name'")
        print(f"   )")
        print(f"   response = client.ask('Hello!')")
    else:
        print(f"\n❌ API found on port {api_port} but not working properly.")

if __name__ == "__main__":
    main()
