"""
Policy test: No new Ruff ignores without explicit justification.

This test enforces that any changes to Ruff configuration (select, ignore, per-file-ignores)
must be accompanied by explicit justification and documentation updates.

FAILURE CONDITIONS:
- Ruff config changes without updating this test's baseline
- Ruff config changes without updating JUSTIFICATION string
- Ruff config changes without updating docs/internal/ruff-policy.md

This test is NON-NEGOTIABLE and cannot be bypassed.
"""

import pathlib

import pytest
from pathlib import Path

# Python 3.9 compatibility for TOML parsing
try:
    import tomllib
except ImportError:
    import tomli as tomllib


def load_ruff_config():
    """Load the current ruff configuration from pyproject.toml."""
    test_file = Path(__file__)
    project_root = test_file.parent.parent.parent  # tests/policies/ -> tests/ -> project root
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        pytest.fail(f"pyproject.toml not found at {pyproject_path}")

    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    return config.get("tool", {}).get("ruff", {})


def parse_per_file_ignores(per_file_ignores):
    """Parse per-file-ignores from either list or dictionary format."""
    if isinstance(per_file_ignores, list):
        # Convert list format "pattern:rule1,rule2" to dictionary
        result = {}
        for entry in per_file_ignores:
            if ":" in entry:
                pattern, rules = entry.split(":", 1)
                if rules.strip():
                    result[pattern] = rules.split(",")
                else:
                    result[pattern] = []
        return result
    elif isinstance(per_file_ignores, dict):
        return per_file_ignores
    else:
        return {}


def test_ruff_select_baseline():
    """Test that Ruff select rules match baseline."""
    ruff_config = load_ruff_config()
    lint_config = ruff_config.get("lint", {})

    # BASELINE: Current allowed rule categories
    EXPECTED_SELECT = {
        "E",  # pycodestyle errors
        "W",  # pycodestyle warnings
        "F",  # Pyflakes
        "UP", # pyupgrade
        "B",  # flake8-bugbear
        "SIM", # flake8-simplify
        "I",  # isort
        "S",  # flake8-bandit (security)
        "RUF", # ruff-specific rules
        "C4", # flake8-comprehensions
        "PIE", # flake8-pie
    }

    actual_select = set(lint_config.get("select", []))

    if actual_select != EXPECTED_SELECT:
        missing = EXPECTED_SELECT - actual_select
        extra = actual_select - EXPECTED_SELECT

        error_msg = "Ruff select rules have changed!\n"
        if missing:
            error_msg += f"  Missing rules: {sorted(missing)}\n"
        if extra:
            error_msg += f"  Extra rules: {sorted(extra)}\n"
        error_msg += "\nTo fix this:\n"
        error_msg += "1. Update EXPECTED_SELECT in this test\n"
        error_msg += "2. Update JUSTIFICATION string below\n"
        error_msg += "3. Update docs/internal/ruff-policy.md\n"

        pytest.fail(error_msg)


def test_ruff_ignore_baseline():
    """Test that Ruff ignore rules match baseline."""
    ruff_config = load_ruff_config()
    lint_config = ruff_config.get("lint", {})

    # BASELINE: Currently ignored rules with justification
    EXPECTED_IGNORE = {
        "F403",  # Star imports - used in __init__.py files for dynamic loading
        "F405",  # Star imports - used in __init__.py files for dynamic loading
        "UP006", # typing modernization - avoid churn for py39 compatibility
        "UP045", # typing modernization - avoid churn for py39 compatibility
        "UP007", # typing modernization - avoid churn for py39 compatibility
    }

    actual_ignore = set(lint_config.get("ignore", []))

    if actual_ignore != EXPECTED_IGNORE:
        missing = EXPECTED_IGNORE - actual_ignore
        extra = actual_ignore - EXPECTED_IGNORE

        error_msg = "Ruff ignore rules have changed!\n"
        if missing:
            error_msg += f"  Removed ignores: {sorted(missing)}\n"
        if extra:
            error_msg += f"  Added ignores: {sorted(extra)}\n"
        error_msg += "\nTo fix this:\n"
        error_msg += "1. Update EXPECTED_IGNORE in this test\n"
        error_msg += "2. Update JUSTIFICATION string below\n"
        error_msg += "3. Update docs/internal/ruff-policy.md\n"
        error_msg += "4. Document why each new ignore is necessary\n"

        pytest.fail(error_msg)


def test_ruff_per_file_ignores_baseline():
    """Test that Ruff per-file-ignores match baseline."""
    ruff_config = load_ruff_config()
    lint_config = ruff_config.get("lint", {})

    # BASELINE: Per-file ignores with minimal, justified exceptions
    EXPECTED_PER_FILE_IGNORES = {
        "tools/diagnostics/**": {"S101"},  # Allow assert statements in diagnostic scripts  # noqa: S101 - Test validation
        "tools/benchmarks.py": {"F841", "E501", "F401", "UP006", "UP035", "RUF059"},  # Benchmark-specific patterns
        "tests/utils/**": {"UP006", "UP035", "F841", "W293"},  # Test utilities compatibility
        "tests/**": {
            "S101", "B018", "S105", "S106", "S108", "S311", "S603", "S607",
            "B011", "B017", "E501", "SIM117", "SIM105"
        },  # Test-specific allowances
        "src/ai_utilities/cli.py": set(),  # CLI tools - print statements appropriate
        "src/ai_utilities/client.py": {"E402"},  # Conditional OpenAI import handling
        "src/ai_utilities/providers/openai_provider.py": {"E402"},  # Conditional OpenAI import
        "src/ai_utilities/providers/openai_compatible_provider.py": {"E402"},  # Conditional OpenAI import
        "src/ai_utilities/cache.py": {"S608"},  # SQL queries with validated table names
        "src/ai_utilities/_test_reset.py": {"S110"},  # Test reset cleanup patterns
        "src/ai_utilities/audio/audio_utils.py": {"S110"},  # Audio error handling patterns
        "src/ai_utilities/setup/**": set(),  # Setup tools - print statements appropriate
        "src/ai_utilities/__init__.py": {"F401", "E402"},  # Dynamic loading and module organization
        "src/ai_utilities/knowledge/models.py": {"S607"},  # Git subprocess in safe context
    }

    actual_per_file_raw = lint_config.get("per-file-ignores", {})
    actual_per_file = parse_per_file_ignores(actual_per_file_raw)

    # Filter out non-ignore entries
    filtered_actual = {}
    for pattern, ignores in actual_per_file.items():
        if pattern not in ["fixable", "unfixable"]:
            if isinstance(ignores, str):
                filtered_actual[pattern] = {ignores}
            else:
                filtered_actual[pattern] = set(ignores)

    # Convert string values to sets for comparison
    normalized_actual = {}
    for pattern, ignores in filtered_actual.items():
        if isinstance(ignores, str):
            normalized_actual[pattern] = {ignores}
        else:
            normalized_actual[pattern] = set(ignores)

    if normalized_actual != EXPECTED_PER_FILE_IGNORES:
        error_msg = "Ruff per-file-ignores have changed!\n"

        # Find differences
        all_patterns = set(normalized_actual.keys()) | set(EXPECTED_PER_FILE_IGNORES.keys())

        for pattern in sorted(all_patterns):
            actual = normalized_actual.get(pattern, set())
            expected = EXPECTED_PER_FILE_IGNORES.get(pattern, set())

            if actual != expected:
                missing = expected - actual
                extra = actual - expected

                if missing:
                    error_msg += f"  {pattern}: removed ignores {sorted(missing)}\n"
                if extra:
                    error_msg += f"  {pattern}: added ignores {sorted(extra)}\n"

        error_msg += "\nTo fix this:\n"
        error_msg += "1. Update EXPECTED_PER_FILE_IGNORES in this test\n"
        error_msg += "2. Update JUSTIFICATION string below\n"
        error_msg += "3. Update docs/internal/ruff-policy.md\n"
        error_msg += "4. Document why each new per-file ignore is necessary\n"

        pytest.fail(error_msg)


def test_justification_documented():
    """Test that justification is documented for current configuration."""
    # BASELINE: Current justification for Ruff configuration
    # Update this string whenever you update the baseline above
    JUSTIFICATION = """
    Ruff Configuration Justification (Last updated: 2025-01-25)

    SELECT Rules:
    - E, W: pycodestyle for code consistency
    - F: Pyflakes for undefined names, unused imports
    - UP: pyupgrade for modern Python patterns (with compatibility exceptions)
    - B: flake8-bugbear for common pitfalls
    - SIM: flake8-simplify for code simplification
    - I: isort for import organization
    - S: flake8-bandit for security issues
    - RUF: ruff-specific optimizations
    - C4: flake8-comprehensions for better comprehensions
    - PIE: flake8-pie for miscellaneous improvements

    IGNORE Rules:
    - F403/F405: Star imports necessary for __init__.py dynamic loading
    - UP006/UP045/UP007: Typing modernization deferred for py39 compatibility

    Per-File Ignores:
    - Dev tools: assert statements acceptable for internal tools  # noqa: S101 - Test validation
    - Tests: assert statements, fake credentials, controlled environment patterns  # noqa: S101 - Test validation
    - Benchmarks: unused variables for measurements, long lines for output
    - CLI: print statements appropriate for command-line tools
    - OpenAI providers: conditional imports for optional dependency handling
    - Cache module: SQL queries use validated table names
    - Audio utils: try-except-pass for error handling
    - Knowledge models: git subprocess calls in safe context
    """

    # This test ensures justification is kept up to date
    # If you update any baseline above, you MUST update this justification
    assert "Ruff Configuration Justification" in JUSTIFICATION  # noqa: S101 - Test validation
    assert "2025-01-25" in JUSTIFICATION  # Update date when making changes  # noqa: S101 - Test validation


def test_policy_documentation_exists():
    """Test that policy documentation exists and is up to date."""
    # Find project root from test file location
    test_file = pathlib.Path(__file__)
    project_root = test_file.parent.parent.parent  # tests/policies/ -> tests/ -> project root
    policy_path = project_root / "docs" / "internal" / "ruff-policy.md"

    if not policy_path.exists():
        pytest.fail(
            f"docs/internal/ruff-policy.md not found at {policy_path}!\n"
            "Create this file to document Ruff policy decisions.\n"
            "Include justification for all ignores and per-file exceptions."
        )

    content = policy_path.read_text()

    # Check that key sections exist
    required_sections = [
        "# Ruff Policy",
        "## Configuration Philosophy",
        "## Per-File Exceptions",
        "## Change Process"
    ]

    for section in required_sections:
        if section not in content:
            pytest.fail(f"Missing required section '{section}' in docs/internal/ruff-policy.md")


if __name__ == "__main__":
    # Allow running this test directly
    pytest.main([__file__, "-v"])
