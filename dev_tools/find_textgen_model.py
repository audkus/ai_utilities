#!/usr/bin/env python3
"""
TextGen WebUI Model Finder
Helps you find the correct model name for your TextGen WebUI setup
"""

import requests
import json
import sys

def find_model():
    base_urls = [
        "http://127.0.0.1:7860",
        "http://localhost:7860", 
        "http://127.0.0.1:5000",
        "http://localhost:5000"
    ]
    
    api_endpoints = [
        "/v1/models",
        "/api/v1/models", 
        "/api/models",
        "/api/v1/model",
        "/api/model"
    ]
    
    print("🔍 Searching for TextGen WebUI model...")
    
    for base_url in base_urls:
        print(f"\n📡 Checking {base_url}...")
        
        # Check if web interface is available
        try:
            response = requests.get(f"{base_url}/", timeout=2)
            if response.status_code == 200 and "html" in response.text.lower():
                print(f"✅ Web interface found at {base_url}")
                print("🌐 Open this URL in your browser to see the model name")
                print(f"   👉 {base_url}")
        except:
            pass
        
        # Check API endpoints
        for endpoint in api_endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ API found at {base_url}{endpoint}")
                    
                    if "data" in data and data["data"]:
                        models = [model.get("id", "unknown") for model in data["data"]]
                        print(f"🤖 Available models: {', '.join(models[:3])}")
                        return models[0] if models else None
                    elif "model_name" in data:
                        print(f"🤖 Current model: {data['model_name']}")
                        return data["model_name"]
                    elif "model" in data:
                        print(f"🤖 Current model: {data['model']}")
                        return data["model"]
                        
            except Exception as e:
                continue
    
    print("\n❌ Could not automatically detect model")
    print("\n📝 Manual steps:")
    print("1. Open http://127.0.0.1:7860 in your browser")
    print("2. Look for the model dropdown or current model name")
    print("3. Common model names:")
    print("   - llama-2-7b-chat")
    print("   - vicuna-7b-v1.5") 
    print("   - mistral-7b-instruct")
    print("   - codellama-7b-instruct")
    
    return None

if __name__ == "__main__":
    model = find_model()
    if model:
        print(f"\n🎯 Found model: {model}")
        print(f"📝 Set this in your .env file:")
        print(f"   TEXT_GENERATION_WEBUI_MODEL={model}")
    else:
        print("\n❓ Please check the web interface manually")
