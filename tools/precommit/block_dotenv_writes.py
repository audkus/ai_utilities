#!/usr/bin/env python3
"""
Pre-commit hook to block writing to .env files.

This hook scans staged diffs for patterns that indicate writing to .env files
and blocks commits that contain such patterns to prevent accidental mutation
of secrets/configuration files.
"""

import os
import re
import subprocess
import sys
from typing import List, Tuple


# Patterns that indicate writing to .env files
ENV_WRITE_PATTERNS = [
    # Python patterns
    r'open\s*\(\s*["\']\.env(\.\w+)?["\']\s*,\s*["\'][wa]["\']',
    r'open\s*\(\s*["\']\.env(\.\w+)?["\']\s*,\s*mode\s*=\s*["\'][wa]["\']',
    r'Path\s*\(\s*["\']\.env(\.\w+)?["\']\s*\)\.write_text',
    r'Path\s*\(\s*["\']\.env(\.\w+)?["\']\s*\)\.write_bytes',
    r'["\']\.env(\.\w+)?["\'].*\.write\s*\(',
    
    # Node.js patterns
    r'fs\.writeFileSync\s*\(\s*["\']\.env(\.\w+)?["\']',
    r'fs\.appendFileSync\s*\(\s*["\']\.env(\.\w+)?["\']',
    
    # Shell patterns
    r'>\s*\.env(\.\w+)?',
    r'>>\s*\.env(\.\w+)?',
    r'tee\s+\.env(\.\w+)?',
    r'cat\s+<<\w+>\s*\.env(\.\w+)?',
    r'echo\s+.*>>\s*\.env(\.\w+)?',
    r'echo\s+.*>\s*\.env(\.\w+)?',
    r'printf\s+.*>>\s*\.env(\.\w+)?',
    r'printf\s+.*>\s*\.env(\.\w+)?',
]

# Compile patterns for efficiency
COMPILED_PATTERNS = [re.compile(pattern) for pattern in ENV_WRITE_PATTERNS]

# Files that are allowed to be written to
ALLOWED_TARGETS = {
    '.env.example',
    '.env.template',
    '.env.sample',
    '.env.dist',
}


def get_staged_diff() -> str:
    """Get the staged diff using git diff --cached -U0."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '-U0'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error getting staged diff: {e}")
        sys.exit(1)


def find_violations(diff_text: str) -> List[Tuple[str, int, str]]:
    """
    Find violations in the diff text.
    
    Args:
        diff_text: The git diff output
        
    Returns:
        List of tuples (filename, line_number, matched_line)
    """
    violations = []
    lines = diff_text.split('\n')
    
    current_file = None
    current_line = None
    
    for line in lines:
        # Parse diff headers
        if line.startswith('+++ b/'):
            # Extract filename from +++ b/filename
            filename = line[6:]  # Remove '+++ b/'
            current_file = filename
            continue
        
        if line.startswith('@@'):
            # Parse line number from @@ -start,count +start,count @@
            # We want the new line number (after +)
            match = re.search(r'\+ *(\d+)', line)
            if match:
                current_line = int(match.group(1)) - 1  # -1 because we increment before processing
            continue
        
        # Only check added lines (start with +)
        if not line.startswith('+'):
            continue
        
        # Increment line number for added lines
        if current_line is not None:
            current_line += 1
        
        # Get the content without the + prefix
        content = line[1:]
        
        # Check against patterns
        for pattern in COMPILED_PATTERNS:
            if pattern.search(content):
                # Check if this is writing to an allowed target
                # Extract the .env filename from the pattern match
                env_match = re.search(r'["\'](\.env(\.\w+)?)["\']', content)
                if env_match:
                    env_filename = env_match.group(1)
                    # Allow writing to .env.example, .env.template, etc.
                    if env_filename in ALLOWED_TARGETS:
                        continue  # Skip this violation
                
                violations.append((current_file or 'unknown', current_line or 0, content))
                break  # Stop checking other patterns for this line
    
    return violations


def print_error_message(violations: List[Tuple[str, int, str]]) -> None:
    """Print a clear error message about violations."""
    print("❌ Pre-commit hook failed: Detected .env file write patterns")
    print()
    print("The following lines attempt to write to .env files:")
    print()
    
    for filename, line_num, content in violations[:20]:  # Limit to 20 violations
        print(f"  {filename}:{line_num}")
        print(f"    {content}")
        print()
    
    if len(violations) > 20:
        print(f"  ... and {len(violations) - 20} more violations")
        print()
    
    print("🛠️  How to fix:")
    print("  • Do not write to .env files from scripts")
    print("  • Print instructions for users to manually edit .env")
    print("  • Write to .env.local or other user-specific files if needed")
    print("  • Use .env.example as a template for documentation")
    print()
    print("This hook prevents accidental mutation of secrets and configuration files.")


def main() -> None:
    """Main entry point for the pre-commit hook."""
    diff_text = get_staged_diff()
    violations = find_violations(diff_text)
    
    if violations:
        print_error_message(violations)
        sys.exit(1)
    
    print("✅ No .env write patterns detected")
    sys.exit(0)


if __name__ == "__main__":
    main()
