"""Environment detection utilities for safe interactive operations.

This module provides utilities to detect if we're running in an environment
where interactive input is safe or would cause blocking issues.
"""

import os
import sys
from typing import Optional


def is_interactive_environment() -> bool:
    """Check if we're running in an interactive environment where input() is safe.
    
    Returns:
        True if interactive input is safe, False if it would block/hang
    """
    # Check for explicit CI environment variables
    ci_indicators = [
        "CI",                    # Generic CI indicator
        "CONTINUOUS_INTEGRATION", # Generic CI
        "GITHUB_ACTIONS",        # GitHub Actions
        "GITLAB_CI",             # GitLab CI
        "TRAVIS",                # Travis CI
        "CIRCLECI",              # CircleCI
        "JENKINS_URL",           # Jenkins
        "AZURE_PIPELINES",       # Azure DevOps
        "BITBUCKET_BUILD_NUMBER", # Bitbucket
        "APPVEYOR",              # AppVeyor
        "CODEBUILD_BUILD_ID",    # AWS CodeBuild
        "GOOGLE_CLOUD_PROJECT",  # Google Cloud Build
        "BUILDKITE",             # Buildkite
    ]
    
    if any(os.getenv(var) for var in ci_indicators):
        return False
    
    # Check for pytest (testing environment)
    if "PYTEST_CURRENT_TEST" in os.environ or "pytest" in sys.modules:
        return False
    
    # Check if stdin is a TTY (terminal)
    if not sys.stdin.isatty():
        return False
    
    # Check for common non-interactive shells
    shell = os.getenv("SHELL", "")
    if any(pattern in shell.lower() for pattern in ["nologin", "false"]):
        return False
    
    # Check for Docker/container environments
    if os.getenv("DOCKER_CONTAINER"):
        return False
    
    # Check for systemd/cron environments
    if os.getenv("INVOCATION_ID"):  # systemd
        return False
    
    # Check if we're running as a daemon/background process
    if os.getenv("DAEMON_PROCESS"):
        return False
    
    # Default to safe (assume interactive if we can't detect non-interactive)
    return True


def is_ci_environment() -> bool:
    """Check if we're running in a CI/CD environment.
    
    Returns:
        True if running in CI/CD, False otherwise
    """
    ci_indicators = [
        "CI",
        "CONTINUOUS_INTEGRATION", 
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "TRAVIS",
        "CIRCLECI",
        "JENKINS_URL",
        "AZURE_PIPELINES",
        "BITBUCKET_BUILD_NUMBER",
        "APPVEYOR",
        "CODEBUILD_BUILD_ID",
        "GOOGLE_CLOUD_PROJECT",
        "BUILDKITE",
    ]
    
    return any(os.getenv(var) for var in ci_indicators)


def is_development_environment() -> bool:
    """Check if we're running in a development environment.
    
    Returns:
        True if development environment, False otherwise
    """
    # Check for common development indicators
    dev_indicators = [
        "VIRTUAL_ENV",           # Python virtual environment
        "CONDA_DEFAULT_ENV",     # Conda environment
        "PYCHARM_HOSTED",        # PyCharm IDE
        "VSCODE_PID",            # VS Code
        "IPython",               # IPython/Jupyter
    ]
    
    return any(os.getenv(var) for var in dev_indicators)


def get_environment_type() -> str:
    """Get a description of the current environment type.
    
    Returns:
        String describing the environment type
    """
    if is_ci_environment():
        return "CI/CD"
    elif not is_interactive_environment():
        return "Non-Interactive"
    elif is_development_environment():
        return "Development"
    else:
        return "Interactive"


def safe_input(prompt: str, default: str = "", timeout: Optional[int] = None) -> str:
    """Safely get user input with fallback for non-interactive environments.
    
    Args:
        prompt: The prompt to display to the user
        default: Default value if input is not possible
        timeout: Optional timeout in seconds (not implemented in this simple version)
        
    Returns:
        User input or default value if input is not possible
    """
    if not is_interactive_environment():
        return default
    
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        return default


def should_prompt_for_reconfigure() -> bool:
    """Determine if we should prompt for reconfiguration.
    
    Returns:
        True if safe to prompt, False if we should skip prompting
    """
    return is_interactive_environment() and not is_ci_environment()


def log_environment_info() -> None:
    """Log information about the current environment for debugging."""
    env_type = get_environment_type()
    interactive = is_interactive_environment()
    ci = is_ci_environment()
    
    print(f"Environment: {env_type}")
    print(f"Interactive: {interactive}")
    print(f"CI/CD: {ci}")
    
    if not interactive:
        print("Non-interactive environment detected - will skip prompts")


if __name__ == "__main__":
    # Test the environment detection
    log_environment_info()
