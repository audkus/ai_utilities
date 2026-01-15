#!/usr/bin/env python3
"""
Import diagnostic script to identify circular dependencies and blocking imports.

This script helps diagnose why certain modules are hanging during import.
"""

import sys
import time
import traceback
import importlib
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_import(module_name, timeout=5):
    """Test importing a module with timeout."""
    print(f"\n🔍 Testing import: {module_name}")
    
    start_time = time.time()
    
    try:
        # Try to import the module
        module = importlib.import_module(module_name)
        end_time = time.time()
        
        print(f"✅ SUCCESS: {module_name} imported in {end_time - start_time:.2f}s")
        return True
        
    except ImportError as e:
        end_time = time.time()
        print(f"❌ IMPORT ERROR: {module_name} - {e}")
        print(f"   Time taken: {end_time - start_time:.2f}s")
        return False
        
    except Exception as e:
        end_time = time.time()
        print(f"❌ ERROR: {module_name} - {type(e).__name__}: {e}")
        print(f"   Time taken: {end_time - start_time:.2f}s")
        traceback.print_exc()
        return False

def test_individual_knowledge_modules():
    """Test each knowledge module individually."""
    print("\n" + "="*60)
    print("🧪 TESTING INDIVIDUAL KNOWLEDGE MODULES")
    print("="*60)
    
    knowledge_modules = [
        "ai_utilities.knowledge.exceptions",
        "ai_utilities.knowledge.models", 
        "ai_utilities.knowledge.chunking",
        "ai_utilities.knowledge.sources",
        "ai_utilities.knowledge.search",
        "ai_utilities.knowledge.indexer",
        "ai_utilities.knowledge.backend",
    ]
    
    results = {}
    
    for module in knowledge_modules:
        results[module] = test_import(module)
        
    return results

def test_metrics_module():
    """Test the metrics module specifically."""
    print("\n" + "="*60)
    print("🧪 TESTING METRICS MODULE")
    print("="*60)
    
    return test_import("ai_utilities.metrics")

def test_dependencies():
    """Test basic dependencies."""
    print("\n" + "="*60)
    print("🧪 TESTING BASIC DEPENDENCIES")
    print("="*60)
    
    dependencies = [
        "sqlite3",
        "pydantic",
        "pathlib",
        "threading",
        "logging",
    ]
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} - OK")
        except ImportError as e:
            print(f"❌ {dep} - MISSING: {e}")

def analyze_import_chain():
    """Analyze the import chain to find circular dependencies."""
    print("\n" + "="*60)
    print("🔍 ANALYZING IMPORT CHAIN")
    print("="*60)
    
    # Test step by step imports
    steps = [
        ("Step 1: Basic imports", "ai_utilities.knowledge.exceptions"),
        ("Step 2: Models", "ai_utilities.knowledge.models"),
        ("Step 3: Chunking", "ai_utilities.knowledge.chunking"),
        ("Step 4: Sources", "ai_utilities.knowledge.sources"),
        ("Step 5: Search", "ai_utilities.knowledge.search"),
        ("Step 6: Indexer", "ai_utilities.knowledge.indexer"),
        ("Step 7: Backend", "ai_utilities.knowledge.backend"),
        ("Step 8: Full package", "ai_utilities.knowledge"),
    ]
    
    for step_name, module_name in steps:
        print(f"\n{step_name}:")
        success = test_import(module_name)
        if not success:
            print(f"🛑 STOPPED at {step_name}")
            break

def main():
    """Main diagnostic function."""
    print("🚀 AI UTILITIES IMPORT DIAGNOSTIC")
    print("="*60)
    print(f"Python version: {sys.version}")
    print(f"Working directory: {Path.cwd()}")
    print(f"Python path: {sys.path[:3]}...")
    
    # Test basic dependencies
    test_dependencies()
    
    # Test metrics module
    metrics_result = test_metrics_module()
    
    # Test individual knowledge modules
    knowledge_results = test_individual_knowledge_modules()
    
    # Analyze import chain
    analyze_import_chain()
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    print(f"\n📈 Metrics module: {'✅ PASS' if metrics_result else '❌ FAIL'}")
    
    print(f"\n📈 Knowledge modules:")
    for module, success in knowledge_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {module}: {status}")
    
    failed_modules = [m for m, s in knowledge_results.items() if not s]
    
    if failed_modules:
        print(f"\n🚨 FAILED MODULES: {len(failed_modules)}")
        for module in failed_modules:
            print(f"   - {module}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        print("   1. Check for circular dependencies in failed modules")
        print("   2. Look for module-level code that executes during import")
        print("   3. Check for network/database operations during import")
        print("   4. Consider lazy loading for heavy dependencies")
    else:
        print(f"\n✅ ALL MODULES IMPORTED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
