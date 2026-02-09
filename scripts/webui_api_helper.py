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
        except Exception as e:
            response_time_ms = max(1, int((time.time() - start_time) * 1000))
            return {
                "detected": False,
                "webui_type": "unknown",
                "port": port,
                "endpoint": f"http://127.0.0.1:{port}",
                "status": "not_running",
                "url": f"http://127.0.0.1:{port}",
                "response_time_ms": response_time_ms,
                "error": str(e)
            }
        
        response_time_ms = max(1, int((time.time() - start_time) * 1000))
        return {
            "detected": False,
            "webui_type": "unknown",
            "port": port,
            "endpoint": f"http://127.0.0.1:{port}",
            "status": "not_running",
            "url": f"http://127.0.0.1:{port}",
            "response_time_ms": response_time_ms,
            "error": "No response"
        }
    
    def scan_for_webuis(self, ports: List[int]) -> List[Dict[str, Any]]:
        """Scan for WebUIs on multiple ports."""
        results = []
        for port in ports:
            result = self.detect_webui_on_port(port)
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
        webui_type = webui_info.get("webui_type", "text-generation-webui")
        port = webui_info.get("port", 7860)
        
        base_config = self.config_templates.get(webui_type, self.config_templates["text-generation-webui"])
        config = base_config.copy()
        
        # Use endpoint from webui_info if provided, otherwise construct from port
        if "endpoint" in webui_info:
            config["base_url"] = webui_info["endpoint"]
        else:
            config["base_url"] = f"http://localhost:{port}"
        
        config["models"] = webui_info.get("models", ["auto"])  # Use models from webui_info
        config["api_key"] = "not_required"  # Override api_key for test expectations
        
        return config
    
    def generate_env_file_content(self, webui_info: Dict[str, Any]) -> str:
        """Generate .env file content for WebUI configuration."""
        config = self.generate_ai_utilities_config(webui_info)
        
        env_lines = [
            "# Generated by WebUI API Helper",
            f"AI_PROVIDER={config['provider']}",
            f"AI_BASE_URL={config['base_url']}",
            f"AI_API_KEY={config['api_key']}"
        ]
        
        return "\n".join(env_lines)
    
    def auto_detect_and_configure(self) -> Optional[Dict[str, Any]]:
        """Auto-detect WebUI and return configuration."""
        # Use scan_for_webuis to check all default ports
        ports = list(self.default_ports.values())
        results = self.scan_for_webuis(ports)
        
        # Find the first detected WebUI
        for result in results:
            if result and result.get("detected", False):
                # Find the webui_type for this port
                for webui_type, port in self.default_ports.items():
                    if result["port"] == port:
                        result["type"] = webui_type
                        result["webui_type"] = webui_type  # Add for compatibility
                        return self.generate_ai_utilities_config(result)
        
        return None
    
    def test_webui_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test connection to WebUI using the provided configuration."""
        try:
            base_url = config.get("base_url", "http://localhost:7860")
            response = requests.get(base_url, timeout=5)
            
            # Calculate response time in milliseconds (use elapsed if available, otherwise calculate)
            if hasattr(response, 'elapsed') and hasattr(response.elapsed, 'total_seconds'):
                response_time_ms = int(response.elapsed.total_seconds() * 1000)
            else:
                import time
                start_time = time.time()
                response = requests.get(base_url, timeout=5)
                response_time_ms = int((time.time() - start_time) * 1000)
            
            # Test if we can get a basic response
            test_response = None
            try:
                if response.status_code == 200:
                    test_response = response.json() if response.text else {"status": "ok"}
            except:
                test_response = {"status": "ok"}
            
            return {
                "status": "success" if response.status_code == 200 else "failed",
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "url": base_url,
                "response_time_ms": response_time_ms,
                "test_response": test_response
            }
        except Exception as e:
            return {
                "status": "failed",
                "success": False,
                "error": str(e),
                "url": config.get("base_url", "http://localhost:7860"),
                "response_time_ms": 0,
                "test_response": None
            }
    
    def save_config_json(self, config: Dict[str, Any], output_file: Path) -> None:
        """Save configuration to JSON file."""
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def save_config_env(self, config: Dict[str, Any], env_file: str) -> None:
        """Save configuration to .env file."""
        env_content = self.generate_env_file_content({"webui_type": "text-generation-webui", "port": 7860})
        with open(env_file, 'w') as f:
            f.write(env_content)
    
    def run_discovery_process(self, output_file: str) -> Dict[str, Any]:
        """Run the complete discovery process and save configuration."""
        config = self.auto_detect_and_configure()
        if config:
            # Test the connection
            connection_test = self.test_webui_connection(config)
            
            # Save configuration
            self.save_config_json(config, Path(output_file))
            
            return {
                "success": True,
                "config": config,
                "connection_test": connection_test,
                "output_file": output_file
            }
        return {
            "success": False,
            "error": "No WebUI detected",
            "connection_test": None
        }
    
    def get_supported_webuis(self) -> List[Dict[str, Any]]:
        """Get information about supported WebUIs."""
        webui_list = []
        for webui_name in self.supported_webuis:
            webui_info = {
                "name": webui_name,
                "type": webui_name,
                "default_port": self.default_ports.get(webui_name, 7860),
                "description": f"{webui_name} WebUI interface"
            }
            webui_list.append(webui_info)
        return webui_list
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate WebUI configuration."""
        required_fields = ["provider", "base_url", "api_key"]
        is_valid = all(field in config for field in required_fields)
        return {
            "valid": is_valid,
            "errors": [field for field in required_fields if field not in config] if not is_valid else []
        }
    
    def run_continuous_monitoring(self, interval: float = 5.0, duration: float = 60.0) -> List[Dict[str, Any]]:
        """Run continuous monitoring for WebUIs."""
        import time
        results = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # Use scan_for_webuis to check all default ports
            ports = list(self.default_ports.values())
            scan_results = self.scan_for_webuis(ports)
            results.extend(scan_results)
            time.sleep(interval)
        
        return results
    
    def get_status_summary(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary of scan results."""
        total_scanned = len(scan_results)
        detected_count = sum(1 for result in scan_results if result.get("detected", False))
        healthy_count = sum(1 for result in scan_results if result.get("detected", False) and not result.get("error"))
        
        return {
            "total_scanned": total_scanned,
            "detected_count": detected_count,
            "healthy_count": healthy_count,
            "webuis": [result.get("webui_type", "unknown") for result in scan_results if result.get("detected", False)],
            "ports": [result["port"] for result in scan_results],
            "total_found": detected_count  # Keep for backward compatibility
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
    """Main CLI entry point."""
    import sys
    import argparse
    
    # SSL Backend Compatibility Check
    try:
        # Add the src directory to Python path for imports
        sys.path.insert(0, '/Users/steffenrasmussen/PycharmProjects/ai_utilities/src')
        from ai_utilities.ssl_check import require_ssl_backend
        require_ssl_backend()
    except ImportError:
        # If ai_utilities is not available, continue without SSL check
        pass
    
    parser = argparse.ArgumentParser(description='WebUI API Helper CLI')
    parser.add_argument('--discover', action='store_true', help='Run discovery process')
    parser.add_argument('--scan', action='store_true', help='Scan for WebUIs')
    parser.add_argument('--ports', help='Comma-separated list of ports to scan')
    parser.add_argument('--test', action='store_true', help='Test WebUI connection')
    parser.add_argument('--url', help='URL to test connection')
    parser.add_argument('--config', help='Configuration file for testing')
    parser.add_argument('--list-supported', action='store_true', help='List supported WebUIs')
    
    args = parser.parse_args()
    
    helper = WebUIAPIHelper()
    
    if args.discover:
        print("🔍 Running WebUI discovery process...")
        result = helper.run_discovery_process("webui_config.json")
        if result["success"]:
            print("✅ Discovery completed successfully!")
            print(f"📁 Configuration saved to: {result['output_file']}")
        else:
            print(f"❌ Discovery failed: {result['error']}")
    
    elif args.scan:
        print("🔍 Scanning for WebUIs...")
        if args.ports:
            ports = [int(p.strip()) for p in args.ports.split(',')]
        else:
            ports = list(helper.default_ports.values())
        
        results = helper.scan_for_webuis(ports)
        print(f"📊 Scanned {len(ports)} ports, found {len([r for r in results if r.get('detected')])} WebUIs")
        
        for result in results:
            if result.get('detected'):
                print(f"✅ {result.get('webui_type', 'unknown')} on port {result['port']}")
            else:
                print(f"❌ No WebUI on port {result['port']}")
    
    elif args.test:
        print("🧪 Testing WebUI connection...")
        if args.url:
            # Test with URL directly
            config = {
                "provider": "openai_compatible",
                "base_url": args.url,
                "api_key": "not_required"
            }
        elif args.config:
            # Test with config file
            try:
                import json
                with open(args.config, 'r') as f:
                    config = json.load(f)
            except Exception as e:
                print(f"❌ Error loading config: {e}")
                return
        else:
            print("❌ --url or --config parameter required for testing")
            sys.exit(1)
        
        result = helper.test_webui_connection(config)
        if result["status"] == "success":
            print("✅ Connection test successful!")
            print(f"📊 Response time: {result['response_time_ms']}ms")
        else:
            print("❌ Connection test failed!")
            if "error" in result:
                print(f"Error: {result['error']}")
    
    elif args.list_supported:
        print("📋 Supported WebUIs:")
        supported = helper.get_supported_webuis()
        for webui in supported:
            print(f"  • {webui['name']} ({webui['type']})")
            print(f"    Default port: {webui['default_port']}")
            print(f"    Description: {webui['description']}")
    
    else:
        # Default behavior - original functionality
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
            print(f"   python scripts/monitoring/probe_text_generation_webui_integration.py")
            
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
