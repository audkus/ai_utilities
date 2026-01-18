#!/usr/bin/env python3
"""Simple test to verify coverage works."""

import sys
sys.path.insert(0, 'src')

# Import the module
from ai_utilities.error_codes import ErrorCode, create_error

# Call some functions
print("Testing error_codes...")

# This should generate coverage
error1 = create_error(ErrorCode.CONFIG_MISSING_API_KEY, "Test message 1")
error2 = create_error(ErrorCode.PROVIDER_UNREACHABLE, "Test message 2")

print(f"Created errors: {error1}, {error2}")

# Access enum values
codes = [
    ErrorCode.CONFIG_MISSING_API_KEY,
    ErrorCode.PROVIDER_UNREACHABLE,
    ErrorCode.CACHE_CONNECTION_FAILED,
    ErrorCode.FILE_NOT_FOUND,
    ErrorCode.USAGE_TRACKING_FAILED,
    ErrorCode.JSON_PARSE_FAILED,
    ErrorCode.CAPABILITY_NOT_SUPPORTED,
    ErrorCode.SYSTEM_MEMORY_ERROR,
    ErrorCode.UNKNOWN_ERROR
]

for code in codes:
    print(f"Code: {code.name} = {code.value}")

print("Test completed successfully!")
