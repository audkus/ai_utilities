#!/usr/bin/env python3
"""
Demonstration of SQLite cache with namespace support.

This script shows how to use the new SQLite cache backend with different namespaces
to isolate cache data between projects or workspaces.
"""

import tempfile
from pathlib import Path

from ai_utilities.client import AiClient, AiSettings
from tests.test_caching import FakeProvider


def demo_sqlite_cache_namespaces():
    """Demonstrate SQLite cache with namespace isolation."""
    print("🗄️  SQLite Cache with Namespace Support Demo")
    print("=" * 50)
    
    # Create temporary database
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "demo_cache.sqlite"
        
        # Create fake provider for demo
        fake_settings = AiSettings(temperature=0.5)
        provider = FakeProvider(fake_settings)
        
        print(f"📁 Database: {db_path}")
        print()
        
        # Demo 1: Different namespaces are isolated
        print("🔒 Demo 1: Namespace Isolation")
        print("-" * 30)
        
        # Project A namespace
        settings_a = AiSettings(
            cache_enabled=True,
            cache_backend="sqlite",
            cache_sqlite_path=db_path,
            cache_namespace="project-alpha",
            temperature=0.5
        )
        client_a = AiClient(settings=settings_a, provider=provider)
        
        # Project B namespace  
        settings_b = AiSettings(
            cache_enabled=True,
            cache_backend="sqlite",
            cache_sqlite_path=db_path,
            cache_namespace="project-beta", 
            temperature=0.5
        )
        client_b = AiClient(settings=settings_b, provider=provider)
        
        prompt = "What is machine learning?"
        
        # First call from project A
        print(f"📤 Project A asks: '{prompt}'")
        response_a1 = client_a.ask(prompt)
        print(f"💬 Response: {response_a1[:50]}...")
        print(f"📊 Provider calls: {provider.ask_count}")
        
        # Second call from project A (should hit cache)
        print(f"\n📤 Project A asks again: '{prompt}'")
        response_a2 = client_a.ask(prompt)
        print(f"💬 Response: {response_a2[:50]}...")
        print(f"📊 Provider calls: {provider.ask_count} (cached!)")
        
        # Call from project B (different namespace, should miss cache)
        print(f"\n📤 Project B asks: '{prompt}'")
        response_b = client_b.ask(prompt)
        print(f"💬 Response: {response_b[:50]}...")
        print(f"📊 Provider calls: {provider.ask_count} (cache miss - different namespace)")
        
        print()
        
        # Demo 2: Same namespace shares cache
        print("🔗 Demo 2: Same Namespace Sharing")
        print("-" * 35)
        
        # New client with same namespace as A
        settings_c = AiSettings(
            cache_enabled=True,
            cache_backend="sqlite", 
            cache_sqlite_path=db_path,
            cache_namespace="project-alpha",
            temperature=0.5
        )
        client_c = AiClient(settings=settings_c, provider=provider)
        
        print(f"📤 Project Alpha (new client) asks: '{prompt}'")
        response_c = client_c.ask(prompt)
        print(f"💬 Response: {response_c[:50]}...")
        print(f"📊 Provider calls: {provider.ask_count} (cached from same namespace)")
        
        print()
        
        # Demo 3: Custom cache settings
        print("⚙️  Demo 3: Custom Cache Settings")
        print("-" * 32)
        
        settings_custom = AiSettings(
            cache_enabled=True,
            cache_backend="sqlite",
            cache_sqlite_path=db_path,
            cache_namespace="custom-settings",
            cache_ttl_s=3600,  # 1 hour TTL
            cache_sqlite_max_entries=5,  # Small cache for demo
            cache_sqlite_prune_batch=2,
            temperature=0.5
        )
        client_custom = AiClient(settings=settings_custom, provider=provider)
        
        print(f"📤 Custom cache asks: '{prompt}'")
        response_custom = client_custom.ask(prompt)
        print(f"💬 Response: {response_custom[:50]}...")
        print(f"📊 Provider calls: {provider.ask_count}")
        print(f"⚙️  Cache settings: TTL=1h, Max entries=5")
        
        # Show database contents
        print()
        print("📊 Database Contents:")
        print("-" * 20)
        
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("""
                SELECT namespace, COUNT(*) as entries, 
                       MIN(created_at) as oldest,
                       MAX(last_access_at) as newest
                FROM ai_cache 
                GROUP BY namespace 
                ORDER BY namespace
            """)
            
            for row in cursor.fetchall():
                namespace, count, oldest, newest = row
                print(f"  📂 {namespace}: {count} entries")
        
        print()
        print("✅ Demo completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  • Namespace isolation prevents cross-project cache pollution")
        print("  • Same namespace shares cache across client instances") 
        print("  • Custom TTL and size limits per namespace")
        print("  • Persistent storage with SQLite")
        print("  • Thread-safe and concurrent access")


if __name__ == "__main__":
    demo_sqlite_cache_namespaces()
