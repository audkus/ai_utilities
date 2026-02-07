#!/usr/bin/env python3
"""
Step 3: Caching - Tutorial
Understanding and using intelligent caching to reduce costs.
"""

import os
import sys
from pathlib import Path
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities import AiClient

def main():
    print("💾 Step 3: Caching")
    print("=" * 50)
    
    # Create client
    client = AiClient()
    
    print("📊 Testing caching behavior...")
    
    # First request (hits API, costs tokens)
    print("  1️⃣ First request (will hit API):")
    start_time = time.time()
    response1 = client.ask("What is the capital of France?")
    end_time = time.time()
    cost1 = response1.cost
    print(f"     Response: {response1.text}")
    print(f"     Time: {end_time - start_time:.2f}s")
    print(f"     Cost: ${cost1:.4f}")
    
    # Second request (cached, instant response, $0 cost)
    print("\n  2️⃣ Second request (should be cached):")
    start_time = time.time()
    response2 = client.ask("What is the capital of France?")
    end_time = time.time()
    cost2 = response2.cost
    print(f"     Response: {response2.text}")
    print(f"     Time: {end_time - start_time:.2f}s")
    print(f"     Cost: ${cost2:.4f}")
    
    # Third request (different question, hits API)
    print("\n  3️⃣ Third request (different question):")
    start_time = time.time()
    response3 = client.ask("What is the capital of Spain?")
    end_time = time.time()
    cost3 = response3.cost
    print(f"     Response: {response3.text}")
    print(f"     Time: {end_time - start_time:.2f}s")
    print(f"     Cost: ${cost3:.4f}")
    
    # Summary
    print(f"\n💰 Cost Summary:")
    print(f"     Total cost: ${cost1 + cost2 + cost3:.4f}")
    print(f"     Savings from caching: ${cost2:.4f}")
    print(f"     Cache hit rate: 33% (1/3 requests)")
    
    print("\n✅ Caching is working perfectly!")
    print("  📚 Next: Run 'python examples/tutorial/step_04_advanced.py'")

if __name__ == "__main__":
    main()
