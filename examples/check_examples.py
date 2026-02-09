#!/usr/bin/env python3
"""
Examples Sanity Check

Simple script to verify that all example scripts can be imported
and have basic syntax validation.
"""

import ast
import sys
from pathlib import Path


def check_python_syntax(file_path: Path) -> bool:
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST to check syntax
        ast.parse(content)
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking {file_path}: {e}")
        return False


def main():
    """Check all Python files in examples directory."""
    print("🔍 Examples Sanity Check")
    print("=" * 40)
    
    examples_dir = Path(__file__).parent
    python_files = list(examples_dir.rglob("*.py"))
    
    # Exclude the check script itself
    python_files = [f for f in python_files if f.name != "check_examples.py"]
    
    print(f"Found {len(python_files)} Python files to check")
    
    passed = 0
    failed = 0
    
    for file_path in sorted(python_files):
        relative_path = file_path.relative_to(examples_dir)
        print(f"\n🔍 Checking: {relative_path}")
        
        if check_python_syntax(file_path):
            print(f"   ✅ Syntax OK")
            passed += 1
        else:
            print(f"   ❌ Syntax Error")
            failed += 1
    
    print(f"\n📊 Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📁 Total:  {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All examples passed syntax check!")
        return 0
    else:
        print(f"\n⚠️  {failed} files have syntax issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())
