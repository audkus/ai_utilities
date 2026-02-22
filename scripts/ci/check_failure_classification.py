#!/usr/bin/env python3
"""Check pytest failure classification for blocked test failures.

This script reads .pytest_artifacts/failure_classification.json and exits
with appropriate codes based on the presence of blocked test failures.

Used in CI workflows to enforce that blocked test failures (collection/setup
failures that prevent proper test execution) must be fixed before other
test failures can be addressed.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def read_failure_classification(file_path: Path) -> Dict[str, Any]:
    """Read and parse the failure classification JSON file.
    
    Args:
        file_path: Path to the failure classification JSON file
        
    Returns:
        Parsed JSON data as dictionary
        
    Raises:
        SystemExit: If file is missing or invalid JSON
    """
    if not file_path.exists():
        print("❌ CI FAILED: Failure classification JSON not found")
        print("This indicates a fundamental issue with test execution or plugin failure.")
        sys.exit(1)
    
    try:
        with file_path.open('r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("❌ CI FAILED: Failure classification JSON is invalid")
        print("The JSON file exists but contains malformed data.")
        sys.exit(1)


def get_blocked_count(data: Dict[str, Any]) -> int:
    """Extract blocked count from failure classification data.
    
    Args:
        data: Parsed failure classification data
        
    Returns:
        Number of blocked test failures (0 if not specified)
    """
    return int(data.get('blocked_count', 0))


def get_blocked_nodeids(data: Dict[str, Any]) -> List[str]:
    """Extract blocked node IDs from failure classification data.
    
    Args:
        data: Parsed failure classification data
        
    Returns:
        List of blocked test node IDs (empty if not specified)
    """
    return data.get('blocked_nodeids', [])


def print_blocked_nodeids(nodeids: List[str], max_display: int = 10) -> None:
    """Print blocked test node IDs with truncation if too many.
    
    Args:
        nodeids: List of blocked test node IDs
        max_display: Maximum number of node IDs to display
    """
    if not nodeids:
        return
    
    print("Failure details:")
    displayed_nodeids = nodeids[:max_display]
    for nodeid in displayed_nodeids:
        print(f"  - {nodeid}")
    
    if len(nodeids) > max_display:
        remaining = len(nodeids) - max_display
        print(f"  ... and {remaining} more")


def main() -> None:
    """Main entry point for the failure classification check."""
    # Path to the failure classification JSON file
    json_file = Path(".pytest_artifacts/failure_classification.json")
    
    # Read and parse the JSON file
    data = read_failure_classification(json_file)
    
    # Extract blocked count and node IDs
    blocked_count = get_blocked_count(data)
    blocked_nodeids = get_blocked_nodeids(data)
    
    # Check for blocked failures
    if blocked_count > 0:
        print(f"❌ CI FAILED: {blocked_count} blocked test(s) detected")
        print("Blocked tests indicate collection or setup failures that prevent proper test execution.")
        print("These must be fixed before other test failures can be addressed.")
        print("")
        print_blocked_nodeids(blocked_nodeids)
        sys.exit(1)
    else:
        print("✅ No blocked test failures detected")
        sys.exit(0)


if __name__ == "__main__":
    main()
