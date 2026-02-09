"""
Plugin to detect early ai_utilities imports during pytest collection.

This plugin monitors sys.modules during pytest collection and records
any ai_utilities modules that are imported before test execution starts.
"""

import sys


def pytest_configure(config):
    """Called after command line options have been parsed."""
    # Store initial state before any imports happen
    initial_modules = set(sys.modules.keys())
    config._early_ai_utilities_modules = {
        mod for mod in initial_modules if mod.startswith("ai_utilities")
    }
    config._collection_started = True


def pytest_collection(session):
    """Called during collection."""
    # Check for any new ai_utilities modules imported during collection
    current_modules = set(sys.modules.keys())
    new_ai_modules = {
        mod for mod in current_modules
        if mod.startswith("ai_utilities") and mod not in session.config._early_ai_utilities_modules
    }

    if new_ai_modules:
        session.config._early_ai_utilities_modules.update(new_ai_modules)
        print(f"WARNING: ai_utilities modules imported during collection: {sorted(new_ai_modules)}")


def pytest_report_header(config):
    """Called to add info to report header."""
    early_modules = getattr(config, '_early_ai_utilities_modules', set())
    if early_modules:
        return f"Early ai_utilities imports detected: {len(early_modules)} modules"
    return "No early ai_utilities imports detected"
