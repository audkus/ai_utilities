"""Contract-first testing policy enforcement.

This module enforces contract-first testing principles by scanning unit tests
for common violations that couple tests to AI output semantics or SDK imports.
"""

import ast
import os
from pathlib import Path
from typing import List, Tuple, Optional

import pytest


def test_contract_first_policy() -> None:
    """Enforce contract-first testing policy on unit tests."""
    unit_tests_dir = Path(__file__).parent / "unit"
    
    # The tests/unit directory should always exist in this repo
    if not unit_tests_dir.exists():
        raise FileNotFoundError("tests/unit directory not found - this should never happen")
    
    violations = []
    
    # Scan all test files in tests/unit
    for test_file in unit_tests_dir.glob("**/test_*.py"):
        file_violations = _scan_file_for_violations(test_file)
        violations.extend(file_violations)
    
    if violations:
        # Group violations by file for clearer output
        violations_by_file = {}
        for file_path, line, col, message in violations:
            if file_path not in violations_by_file:
                violations_by_file[file_path] = []
            violations_by_file[file_path].append((line, col, message))
        
        # Build failure message
        error_parts = ["Contract-first policy violations found:"]
        for file_path, file_violations in sorted(violations_by_file.items()):
            rel_path = os.path.relpath(file_path)
            error_parts.append(f"\n{rel_path}:")
            for line, col, message in sorted(file_violations):
                error_parts.append(f"  Line {line}, Column {col}: {message}")
        
        pytest.fail("\n".join(error_parts))


def _scan_file_for_violations(file_path: Path) -> List[Tuple[Path, int, int, str]]:
    """Scan a single Python file for contract violations."""
    violations = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        
        for node in ast.walk(tree):
            # Rule 1: Check for AI-output semantic substring assertions
            if isinstance(node, ast.Assert):
                violation = _check_assert_violation(node, file_path)
                if violation:
                    violations.append(violation)
                # Rule 3: Check for AI-output equality assertions
                violation = _check_equality_violation(node, file_path)
                if violation:
                    violations.append(violation)
            
            # Rule 2: Check for OpenAI imports
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    violation = _check_openai_import_violation(node, file_path)
                    # Rule 4: Check for other HTTP client imports
                    if not violation:
                        violation = _check_http_import_violation(node, file_path)
                else:
                    violation = _check_openai_import_from_violation(node, file_path)
                    # Rule 4: Check for other HTTP client from imports
                    if not violation:
                        violation = _check_http_import_from_violation(node, file_path)
                if violation:
                    violations.append(violation)
    
    except (SyntaxError, UnicodeDecodeError):
        # Skip files that can't be parsed
        pass
    
    return violations


def _check_assert_violation(node: ast.Assert, file_path: Path) -> Optional[Tuple[Path, int, int, str]]:
    """Check for AI-output semantic substring assertions."""
    if not isinstance(node.test, ast.Compare):
        return None
    
    # Must be "in" comparison
    if not any(isinstance(op, ast.In) for op in node.test.ops):
        return None
    
    # Left side must be string literal
    left = node.test.left
    if not isinstance(left, ast.Constant) or not isinstance(left.value, str):
        return None
    
    # Right side must be response/result/output/text variable
    right = node.test.comparators[0]
    if not _is_response_variable(right):
        return None
    
    return (
        file_path,
        node.lineno,
        node.col_offset,
        'AI-output semantic assertion detected. This violates contract-first testing. '
        'Assert provider calls/parameters or passthrough instead of asserting "literal" in response/result/output/text.'
    )


def _check_openai_import_violation(node: ast.Import, file_path: Path) -> Optional[Tuple[Path, int, int, str]]:
    """Check for OpenAI imports in unit tests."""
    for alias in node.names:
        if alias.name == "openai":
            return (
                file_path,
                node.lineno,
                node.col_offset,
                'Direct OpenAI import detected. Unit tests should not import SDKs to avoid coupling and contract assumptions.'
            )
    return None


def _check_openai_import_from_violation(node: ast.ImportFrom, file_path: Path) -> Optional[Tuple[Path, int, int, str]]:
    """Check for OpenAI from imports in unit tests."""
    if node.module == "openai":
        return (
            file_path,
            node.lineno,
            node.col_offset,
            'Direct OpenAI import detected. Unit tests should not import SDKs to avoid coupling and contract assumptions.'
        )
    return None


def _check_equality_violation(node: ast.Assert, file_path: Path) -> Optional[Tuple[Path, int, int, str]]:
    """Check for AI-output equality assertions."""
    if not isinstance(node.test, ast.Compare):
        return None
    
    # Must be equality comparison
    if not any(isinstance(op, ast.Eq) for op in node.test.ops):
        return None
    
    # Must have exactly one comparison
    if len(node.test.ops) != 1 or len(node.test.comparators) != 1:
        return None
    
    left = node.test.left
    right = node.test.comparators[0]
    
    # One side must be string literal, other must be response-like variable
    left_is_string = isinstance(left, ast.Constant) and isinstance(left.value, str)
    right_is_string = isinstance(right, ast.Constant) and isinstance(right.value, str)
    
    if left_is_string and _is_response_variable(right):
        return (
            file_path,
            node.lineno,
            node.col_offset,
            'Contract-first violation: unit test asserts AI output equals a literal string. '
            'Assert provider calls/parameters or passthrough instead of asserting response == "literal".'
        )
    elif right_is_string and _is_response_variable(left):
        return (
            file_path,
            node.lineno,
            node.col_offset,
            'Contract-first violation: unit test asserts AI output equals a literal string. '
            'Assert provider calls/parameters or passthrough instead of asserting "literal" == response.'
        )
    
    return None


def _check_http_import_violation(node: ast.Import, file_path: Path) -> Optional[Tuple[Path, int, int, str]]:
    """Check for HTTP client imports in unit tests."""
    for alias in node.names:
        if alias.name in {"requests", "httpx", "aiohttp"}:
            return (
                file_path,
                node.lineno,
                node.col_offset,
                'Contract-first violation: importing requests/httpx/aiohttp in unit tests. '
                'Use mocks or move to integration tests.'
            )
    return None


def _check_http_import_from_violation(node: ast.ImportFrom, file_path: Path) -> Optional[Tuple[Path, int, int, str]]:
    """Check for HTTP client from imports in unit tests."""
    if node.module in {"requests", "httpx", "aiohttp"}:
        return (
            file_path,
            node.lineno,
            node.col_offset,
            'Contract-first violation: importing requests/httpx/aiohttp in unit tests. '
            'Use mocks or move to integration tests.'
        )
    return None


def _is_response_variable(node: ast.AST) -> bool:
    """Check if node refers to response/result/output/text variable."""
    if isinstance(node, ast.Name):
        return node.id in {"response", "result", "output", "text"}
    
    elif isinstance(node, ast.Attribute):
        # Check for obj.response, obj.result, etc.
        if isinstance(node.value, ast.Name):
            return node.attr in {"response", "result", "output", "text"}
    
    return False
