#!/usr/bin/env python3
"""
Examples of using ask() with different parameters.

This demonstrates the various parameters you can pass to ask():
- max_tokens: Limit response length
- model: Override the default model
- temperature: Control randomness (0.0-2.0)
- And more...
"""

import os
from ai_utilities import AiClient, AiSettings

def main():
    # Create client with real model
    settings = AiSettings(model="gpt-3.5-turbo")
    client = AiClient(settings)
    
    print("🤖 AI Utilities - ask() Parameter Examples")
    print("=" * 50)
    
    # Example 1: max_tokens parameter
    print("\n1. 📏 Using max_tokens to limit response length:")
    response = client.ask(
        "Explain quantum computing in detail", 
        max_tokens=100
    )
    print(f"Response (limited to 100 tokens): {response}")
    
    # Example 2: model parameter
    print("\n2. 🔄 Using model parameter to override default:")
    response = client.ask(
        "What is the capital of France?", 
        model="gpt-4"  # Override default model
    )
    print(f"Response from gpt-4: {response}")
    
    # Example 3: temperature parameter
    print("\n3. 🌡️ Using temperature to control creativity:")
    print("   Low temperature (0.1):")
    response_low = client.ask(
        "Write a story opening", 
        temperature=0.1
    )
    print(f"   {response_low}")
    
    print("   High temperature (1.5):")
    response_high = client.ask(
        "Write a story opening", 
        temperature=1.5
    )
    print(f"   {response_high}")
    
    # Example 4: Multiple parameters together
    print("\n4. 🎯 Combining multiple parameters:")
    response = client.ask(
        "List 3 programming languages",
        model="gpt-3.5-turbo",
        max_tokens=150,
        temperature=0.3
    )
    print(f"Response: {response}")
    
    # Example 5: JSON format
    print("\n5. 📄 Using JSON return format:")
    response = client.ask(
        "List 3 colors as JSON array",
        return_format="json",
        max_tokens=100
    )
    print(f"JSON Response: {response}")
    
    # Example 6: Batch prompts with parameters
    print("\n6. 📋 Batch prompts with shared parameters:")
    questions = [
        "What is 2+2?",
        "What is 3+3?", 
        "What is 4+4?"
    ]
    responses = client.ask(
        questions,
        max_tokens=50,  # Applied to all questions
        temperature=0.1
    )
    for i, response in enumerate(responses, 1):
        print(f"   Q{i}: {questions[i-1]} -> A: {response}")
    
    print("\n✅ All examples completed!")

if __name__ == "__main__":
    main()
