"""
Parallel AI Calls with Thread-Safe Usage Tracking Example

This example demonstrates how to make multiple AI calls in parallel
while maintaining accurate usage statistics with thread-safe tracking.
"""

import concurrent.futures
import time
from pathlib import Path

# Import the new thread-safe components
from ai_utilities import (
    AiClient, 
    AiSettings, 
    UsageScope, 
    create_usage_tracker,
    ThreadSafeUsageTracker
)


def parallel_ai_calls_example():
    """Example of making parallel AI calls with thread-safe usage tracking."""
    
    print("=== Parallel AI Calls with Thread-Safe Usage Tracking ===\n")
    
    # Example 1: Per-Client Tracking (Default)
    print("1. Per-Client Tracking (Each client has separate stats):")
    client1 = AiClient(track_usage=True)
    client2 = AiClient(track_usage=True)
    
    # Make parallel calls with different clients
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        
        # Submit multiple tasks to different clients
        for i in range(4):
            if i % 2 == 0:
                future = executor.submit(client1.ask, f"What is {i} + {i}?")
            else:
                future = executor.submit(client2.ask, f"What is {i} * {i}?")
            futures.append(future)
        
        # Wait for all to complete
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    print(f"Completed {len(results)} parallel calls")
    client1.print_usage_summary()
    client2.print_usage_summary()
    print()
    
    # Example 2: Per-Process Tracking (Shared within process)
    print("2. Per-Process Tracking (Shared across all clients in this process):")
    
    # Create settings with per-process scope
    settings = AiSettings(usage_scope="per_process")
    client3 = AiClient(settings=settings, track_usage=True)
    client4 = AiClient(settings=settings, track_usage=True)
    
    # Make parallel calls with shared tracking
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = []
        
        # Submit multiple tasks to clients sharing tracking
        questions = [
            "What is the capital of France?",
            "What is the capital of Germany?", 
            "What is the capital of Spain?",
            "What is the capital of Italy?",
            "What is the capital of Portugal?",
            "What is the capital of Greece?"
        ]
        
        for question in questions:
            if len(question) % 2 == 0:
                future = executor.submit(client3.ask, question)
            else:
                future = executor.submit(client4.ask, question)
            futures.append(future)
        
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    print(f"Completed {len(results)} parallel calls")
    client3.print_usage_summary()
    client4.print_usage_summary()
    print()
    
    # Example 3: Custom Client ID Tracking
    print("3. Custom Client ID Tracking:")
    
    # Create settings with custom client ID
    custom_settings = AiSettings(
        usage_scope="per_client",
        usage_client_id="my_parallel_app"
    )
    client5 = AiClient(settings=custom_settings, track_usage=True)
    
    # Make parallel calls
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        questions = [
            "Explain quantum computing in one sentence",
            "Explain machine learning in one sentence", 
            "Explain blockchain in one sentence"
        ]
        
        futures = [executor.submit(client5.ask, q) for q in questions]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    print(f"Completed {len(results)} parallel calls")
    client5.print_usage_summary()
    print()
    
    # Example 4: Aggregated Statistics
    print("4. Aggregated Statistics Across All Scopes:")
    
    # Create a tracker to get aggregated stats
    tracker = create_usage_tracker(scope="per_client")
    aggregated = tracker.get_aggregated_stats()
    
    print(f"Found {len(aggregated)} usage tracking files:")
    total_tokens = 0
    total_requests = 0
    
    for file_path, stats in aggregated.items():
        print(f"  {Path(file_path).name}: {stats.total_tokens} tokens, {stats.total_requests} requests")
        total_tokens += stats.total_tokens
        total_requests += stats.total_requests
    
    print(f"\nTotal across all scopes: {total_tokens} tokens, {total_requests} requests")


def concurrent_stress_test():
    """Stress test with many concurrent calls to verify thread safety."""
    
    print("\n=== Concurrent Stress Test (20 Parallel Calls) ===")
    
    # Create shared tracker
    settings = AiSettings(usage_scope="per_process")
    client = AiClient(settings=settings, track_usage=True)
    
    def make_ai_call(call_id):
        """Make a single AI call."""
        try:
            response = client.ask(f"Call {call_id}: What is 2+2?")
            return f"Call {call_id}: {len(response)} chars"
        except Exception as e:
            return f"Call {call_id}: Error - {e}"
    
    # Make 20 concurrent calls
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(make_ai_call, i) for i in range(20)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    end_time = time.time()
    
    print(f"Completed {len(results)} calls in {end_time - start_time:.2f} seconds")
    print("Sample results:")
    for result in results[:5]:
        print(f"  {result}")
    
    client.print_usage_summary()


def race_condition_demo():
    """Demonstrate that the new implementation prevents race conditions."""
    
    print("\n=== Race Condition Prevention Demo ===")
    
    # Create multiple clients with same custom ID (should share tracking)
    settings = AiSettings(
        usage_scope="per_client",
        usage_client_id="race_condition_test"
    )
    
    clients = [AiClient(settings=settings, track_usage=True) for _ in range(5)]
    
    def rapid_calls(client, client_id):
        """Make rapid calls to stress test the locking."""
        results = []
        for i in range(10):
            try:
                response = client.ask(f"Quick test {i}")
                results.append(f"Client {client_id}-{i}: Success")
            except Exception as e:
                results.append(f"Client {client_id}-{i}: Error")
        return results
    
    # Run concurrent calls from multiple clients
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(rapid_calls, client, i) for i, client in enumerate(clients)]
        all_results = []
        for future in concurrent.futures.as_completed(futures):
            all_results.extend(future.result())
    
    print(f"Completed {len(all_results)} rapid calls across 5 clients")
    
    # All clients should show the same aggregated stats
    print("Stats from each client (should be identical):")
    for i, client in enumerate(clients):
        stats = client.get_stats()
        print(f"  Client {i}: {stats.total_requests} requests, {stats.total_tokens} tokens")
    
    # Verify no data was lost
    expected_requests = 5 * 10  # 5 clients × 10 calls each
    actual_requests = clients[0].get_stats().total_requests
    
    print(f"\nRace condition test:")
    print(f"  Expected requests: {expected_requests}")
    print(f"  Actual requests: {actual_requests}")
    print(f"  Data integrity: {'✅ PASS' if actual_requests == expected_requests else '❌ FAIL'}")


if __name__ == "__main__":
    try:
        parallel_ai_calls_example()
        concurrent_stress_test()
        race_condition_demo()
        
        print("\n=== All Parallel Usage Tracking Examples Completed Successfully! ===")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()
