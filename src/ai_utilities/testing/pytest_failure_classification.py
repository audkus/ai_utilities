"""Pytest plugin for failure classification."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import pytest


class FailureClassificationPlugin:
    """Pytest plugin that classifies test failures by phase."""
    
    def __init__(self) -> None:
        self.blocked_nodeids: List[str] = []
        self.real_nodeids: List[str] = []
        self.teardown_nodeids: List[str] = []
        env_val = os.getenv("AIU_PYTEST_FAILURE_JSON", "").lower()
        self.json_enabled = env_val in ("1", "true")
        self.json_path = Path(".pytest_artifacts/failure_classification.json")
        self.pytest_exitstatus: Optional[int] = None
    
    def _write_json_file(self) -> None:
        """Write current classification state to JSON file."""
        if not self.json_enabled:
            return
            
        # Ensure directory exists
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "blocked_count": len(self.blocked_nodeids),
            "real_count": len(self.real_nodeids),
            "teardown_count": len(self.teardown_nodeids),
            "blocked_nodeids": self.blocked_nodeids[:20],
            "real_nodeids": self.real_nodeids[:20],
            "teardown_nodeids": self.teardown_nodeids[:20],
            "created_utc": time.time(),
            "pytest_exitstatus": self.pytest_exitstatus,
        }
        
        try:
            with open(self.json_path, "w") as f:
                json.dump(data, f, indent=2)
        except OSError:
            # Fail silently if we can't write the file
            pass
    
    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        """Handle collection failures (import errors, syntax errors, etc.)."""
        if report.failed:
            nodeid = report.nodeid
            if nodeid not in self.blocked_nodeids:
                self.blocked_nodeids.append(nodeid)
            self._write_json_file()
    
    @pytest.hookimpl(tryfirst=True, hookwrapper=True)
    def pytest_runtest_makereport(
        self, item: pytest.Item, call: pytest.CallInfo
    ):
        """Classify test failures by phase (setup/call/teardown)."""
        # Execute all other hooks to obtain the report object
        outcome = yield
        report = outcome.get_result()
        
        # Only process if the report indicates failure
        if report.failed:
            nodeid = item.nodeid
            if call.when == "setup":
                if nodeid not in self.blocked_nodeids:
                    self.blocked_nodeids.append(nodeid)
                self._write_json_file()
            elif call.when == "call":
                if nodeid not in self.real_nodeids:
                    self.real_nodeids.append(nodeid)
                self._write_json_file()
            elif call.when == "teardown":
                if nodeid not in self.teardown_nodeids:
                    self.teardown_nodeids.append(nodeid)
                self._write_json_file()
    
    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        """Print summary and finalize JSON file."""
        self.pytest_exitstatus = exitstatus
        
        # Finalize JSON file
        self._write_json_file()
        
        # Print summary only if there are failures
        total_failures = len(self.blocked_nodeids) + len(self.real_nodeids) + len(self.teardown_nodeids)
        if total_failures == 0:
            return
            
        # Print human-readable summary
        print("\n=== Failure Classification ===")
        print(f"BLOCKED: {len(self.blocked_nodeids)}")
        print(f"REAL: {len(self.real_nodeids)}")
        print(f"TEARDOWN: {len(self.teardown_nodeids)}")
        
        if self.blocked_nodeids:
            print("\nBLOCKED:")
            for nodeid in self.blocked_nodeids[:20]:
                print(f"  {nodeid}")
            if len(self.blocked_nodeids) > 20:
                print(f"  ... and {len(self.blocked_nodeids) - 20} more")
        
        if self.real_nodeids:
            print("\nREAL:")
            for nodeid in self.real_nodeids[:20]:
                print(f"  {nodeid}")
            if len(self.real_nodeids) > 20:
                print(f"  ... and {len(self.real_nodeids) - 20} more")
        
        if self.teardown_nodeids:
            print("\nTEARDOWN:")
            for nodeid in self.teardown_nodeids[:20]:
                print(f"  {nodeid}")
            if len(self.teardown_nodeids) > 20:
                print(f"  ... and {len(self.teardown_nodeids) - 20} more")


def pytest_configure(config: pytest.Config) -> None:
    """Register the failure classification plugin."""
    if not hasattr(config, "pluginmanager"):
        return
    
    plugin = FailureClassificationPlugin()
    config.pluginmanager.register(plugin, "failure_classification")
