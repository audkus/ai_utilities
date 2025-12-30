#!/usr/bin/env python3
"""
AI Utilities Test Dashboard

Dynamic test reporting script that provides comprehensive testing overview
including test counts, module support matrix, and production readiness status.

Usage:
    python scripts/test_dashboard.py [--verbose] [--save-report]

Options:
    --verbose       Show detailed test output
    --save-report   Save report to file
    --integration   Run integration tests (requires API key)
"""

import sys
import subprocess
import json
import argparse
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import re

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@dataclass
class TestResult:
    """Test result data structure."""
    category: str
    total: int
    passed: int
    failed: int
    skipped: int
    duration: float
    details: str = ""


@dataclass
class ModuleSupport:
    """Module support information."""
    feature: str
    openai: bool
    openai_compatible: bool
    async_support: bool
    status: str


class TestDashboard:
    """Comprehensive test reporting dashboard."""
    
    def __init__(self):
        self.test_results: List[TestResult] = []
        self.module_support: List[ModuleSupport] = []
        self.start_time = datetime.now()
        
    def run_tests(self, include_integration: bool = False, verbose: bool = False, full_suite: bool = False) -> None:
        """Run all test suites and collect results."""
        # Load environment variables from .env file
        self._load_env_file()
        
        print("🚀 AI UTILITIES TEST DASHBOARD")
        print("=" * 50)
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mode: {'Full Test Suite' if full_suite else 'Files API Focus'}")
        
        # Check if API key is available
        api_key = os.getenv('AI_API_KEY')
        if api_key:
            print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
            integration_available = True
        else:
            print("⚠️  No API Key found - integration tests will be skipped")
            integration_available = False
        print()
        
        if full_suite:
            # Run complete test suite
            self._run_test_suite(
                "Complete Unit Tests",
                ["pytest", "-m", "not integration", "-q"],
                verbose
            )
            
            if include_integration and integration_available:
                self._run_test_suite(
                    "Integration Tests",
                    ["pytest", "-m", "integration", "-q"],
                    verbose
                )
            else:
                print("🧪 Integration Tests (Skipped - No API Key)")
                print("   ⏭️  SKIPPED: Integration tests require API key")
                self.test_results.append(TestResult(
                    category="Integration Tests (Skipped - No API Key)",
                    total=0,
                    passed=0,
                    failed=0,
                    skipped=0,
                    duration=0.0
                ))
                print()
        else:
            # Files API focused tests
            self._run_test_suite(
                "Files API Unit Tests",
                ["pytest", "tests/test_files_api.py", "-q"],
                verbose
            )
            
            if include_integration and integration_available:
                self._run_test_suite(
                    "Files Integration Tests",
                    ["pytest", "tests/test_files_integration_working.py", "-q"],
                    verbose
                )
            else:
                print("🧪 Files Integration Tests (Skipped - No API Key)")
                print("   ⏭️  SKIPPED: Integration tests require API key")
                self.test_results.append(TestResult(
                    category="Files Integration Tests (Skipped - No API Key)",
                    total=0,
                    passed=0,
                    failed=0,
                    skipped=0,
                    duration=0.0
                ))
                print()
        
        # Core functionality tests (always run)
        self._test_core_functionality(verbose)
        self._test_async_operations(verbose)
        
        # Generate module support matrix
        self._generate_module_support_matrix()
    
    def _load_env_file(self):
        """Load environment variables from .env file."""
        from pathlib import Path
        import os
        
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            print(f"📁 Loading environment from: {env_file}")
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
            print("✅ Environment variables loaded")
        else:
            print("⚠️  No .env file found")
        
    def _run_test_suite(self, category: str, command: List[str], verbose: bool) -> None:
        """Run a test suite and parse results."""
        print(f"🧪 Running {category}...")
        
        try:
            if verbose:
                # Show detailed test execution
                print(f"   Command: {' '.join(command)}")
                result = subprocess.run(command, capture_output=False, text=True)
            else:
                # Show progress with live output
                print(f"   Executing: {' '.join(command)}")
                print("   Running tests:")
                
                # Remove -q flag to get live output, add -v for verbose
                cmd = [c for c in command if c != '-q'] + ['-v', '--tb=line']
                env = os.environ.copy()
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    env=env
                )
                
                # Parse individual test lines for progress
                lines = process.stdout.split('\n')
                test_count = 0
                total_tests = 0
                
                for line in lines:
                    line = line.strip()
                    
                    # Get total test count
                    if "collected" in line and "items" in line:
                        match = re.search(r'collected (\d+) items', line)
                        if match:
                            total_tests = int(match.group(1))
                            print(f"   Found {total_tests} tests")
                    
                    # Show individual test results
                    elif "::" in line and ("PASSED" in line or "FAILED" in line or "SKIPPED" in line):
                        test_count += 1
                        parts = line.split("::")
                        if len(parts) > 1:
                            test_name = parts[-1].split()[0]
                            # Shorten test names for display
                            if len(test_name) > 30:
                                test_name = test_name[:27] + "..."
                        else:
                            test_name = "unknown"
                        
                        status = "✅" if "PASSED" in line else "❌" if "FAILED" in line else "⏭️"
                        print(f"   {test_count:2d}/{total_tests:<2d} {status} {test_name}")
                
                result = process
            
            # Parse pytest output for final summary
            output = result.stdout if hasattr(result, 'stdout') else ""
            total, passed, failed, skipped = self._parse_pytest_output(output)
            
            test_result = TestResult(
                category=category,
                total=total,
                passed=passed,
                failed=failed,
                skipped=skipped,
                duration=0.0
            )
            
            self.test_results.append(test_result)
            
            # Show final result
            if failed == 0:
                status = "✅ PASSED"
            elif failed > 0:
                status = "❌ FAILED"
            else:
                status = "⚠️  UNKNOWN"
                
            print(f"   {status}: {passed}/{total} passed")
            if skipped > 0:
                print(f"   ⏭️  {skipped} skipped")
            if failed > 0:
                print(f"   ❌ {failed} failed")
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            self.test_results.append(TestResult(
                category=category,
                total=0,
                passed=0,
                failed=1,
                skipped=0,
                duration=0.0,
                details=str(e)
            ))
        
        print()
    
    def _parse_pytest_output(self, output) -> Tuple[int, int, int, int]:
        """Parse pytest output to extract test counts."""
        # Ensure output is a string
        if not isinstance(output, str):
            output = str(output) if output is not None else ""
        
        # Look for pattern like "24 passed in 0.48s" or "16 skipped in 0.42s"
        passed = len(re.findall(r'passed', output))
        failed = len(re.findall(r'failed', output))
        skipped = len(re.findall(r'skipped', output))
        
        # Extract numbers more precisely
        passed_match = re.search(r'(\d+)\s+passed', output)
        failed_match = re.search(r'(\d+)\s+failed', output)
        skipped_match = re.search(r'(\d+)\s+skipped', output)
        
        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        skipped = int(skipped_match.group(1)) if skipped_match else 0
        
        total = passed + failed + skipped
        
        return total, passed, failed, skipped
    
    def _test_core_functionality(self, verbose: bool) -> None:
        """Test core functionality manually."""
        print("🔧 Testing Core Functionality...")
        
        core_tests = [
            ("Text Generation", self._test_text_generation),
            ("File Upload", self._test_file_upload),
            ("File Download", self._test_file_download),
            ("Image Generation", self._test_image_generation),
            ("Document AI", self._test_document_ai)
        ]
        
        passed = 0
        total = len(core_tests)
        
        for test_name, test_func in core_tests:
            try:
                test_func()
                print(f"   ✅ {test_name}: Working")
                passed += 1
            except Exception as e:
                print(f"   ❌ {test_name}: {e}")
        
        self.test_results.append(TestResult(
            category="Core Functionality",
            total=total,
            passed=passed,
            failed=total - passed,
            skipped=0,
            duration=0.0
        ))
        
        print()
    
    def _test_async_operations(self, verbose: bool) -> None:
        """Test async operations."""
        print("⚡ Testing Async Operations...")
        
        async_tests = [
            ("Async Text Generation", self._test_async_text_generation),
            ("Async Image Generation", self._test_async_image_generation),
            ("Async File Upload", self._test_async_file_upload),
            ("Async File Download", self._test_async_file_download),
            ("Async Document AI", self._test_async_document_ai),
            ("Async Error Handling", self._test_async_error_handling)
        ]
        
        passed = 0
        total = len(async_tests)
        
        for test_name, test_func in async_tests:
            try:
                import asyncio
                asyncio.run(test_func())
                print(f"   ✅ {test_name}: Working")
                passed += 1
            except Exception as e:
                print(f"   ❌ {test_name}: {e}")
        
        self.test_results.append(TestResult(
            category="Async Operations",
            total=total,
            passed=passed,
            failed=total - passed,
            skipped=0,
            duration=0.0
        ))
        
        print()
    
    def _generate_module_support_matrix(self) -> None:
        """Generate module support matrix."""
        print("📊 Generating Module Support Matrix...")
        
        # This would normally check actual provider capabilities
        self.module_support = [
            ModuleSupport("Text Generation", True, True, True, "✅"),
            ModuleSupport("File Upload", True, False, True, "✅"),
            ModuleSupport("File Download", True, False, True, "✅"),
            ModuleSupport("Image Generation", True, False, True, "✅"),
            ModuleSupport("Document AI", True, False, True, "✅"),
            ModuleSupport("Audio Transcription", False, False, False, "🚧"),
            ModuleSupport("Audio Generation", False, False, False, "🚧"),
        ]
        
        print("   ✅ Module matrix generated")
        print()
    
    # Core functionality test methods
    def _test_text_generation(self):
        from ai_utilities import AiClient, AiSettings
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))
        from fake_provider import FakeProvider
        
        settings = AiSettings(api_key='test-key', provider='openai')
        client = AiClient(settings=settings, provider=FakeProvider())
        response = client.ask("Test prompt")
        assert len(response) > 0
    
    def _test_file_upload(self):
        from ai_utilities import AiClient, AiSettings
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))
        from fake_provider import FakeProvider
        import tempfile
        
        settings = AiSettings(api_key='test-key', provider='openai')
        client = AiClient(settings=settings, provider=FakeProvider())
        
        with tempfile.NamedTemporaryFile() as f:
            uploaded = client.upload_file(f.name)
            assert uploaded.file_id is not None
    
    def _test_file_download(self):
        from ai_utilities import AiClient, AiSettings
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))
        from fake_provider import FakeProvider
        
        settings = AiSettings(api_key='test-key', provider='openai')
        client = AiClient(settings=settings, provider=FakeProvider())
        content = client.download_file("test-file-id")
        assert isinstance(content, bytes)
    
    def _test_image_generation(self):
        from ai_utilities import AiClient, AiSettings
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))
        from fake_provider import FakeProvider
        
        settings = AiSettings(api_key='test-key', provider='openai')
        client = AiClient(settings=settings, provider=FakeProvider())
        images = client.generate_image("Test image")
        assert len(images) > 0
    
    def _test_document_ai(self):
        from ai_utilities import AiClient, AiSettings
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))
        from fake_provider import FakeProvider
        
        settings = AiSettings(api_key='test-key', provider='openai')
        client = AiClient(settings=settings, provider=FakeProvider())
        response = client.ask("Analyze document file-123")
        assert len(response) > 0
    
    # Async test methods
    async def _test_async_text_generation(self):
        from ai_utilities import AsyncAiClient, AiSettings
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))
        from test_files_api import create_async_test_client
        
        client = create_async_test_client()
        response = await client.ask("Test prompt")
        assert len(response) > 0
    
    async def _test_async_image_generation(self):
        from ai_utilities import AsyncAiClient, AiSettings
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))
        from test_files_api import create_async_test_client
        
        client = create_async_test_client()
        images = await client.generate_image("Test image")
        assert len(images) > 0
    
    async def _test_async_file_upload(self):
        from ai_utilities import AsyncAiClient, AiSettings
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))
        from test_files_api import create_async_test_client
        import tempfile
        
        client = create_async_test_client()
        with tempfile.NamedTemporaryFile() as f:
            uploaded = await client.upload_file(f.name)
            assert uploaded.file_id is not None
    
    async def _test_async_file_download(self):
        from ai_utilities import AsyncAiClient, AiSettings
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))
        from test_files_api import create_async_test_client
        
        client = create_async_test_client()
        content = await client.download_file("file-123")  # Use correct fake file ID
        assert isinstance(content, bytes)
    
    async def _test_async_document_ai(self):
        from ai_utilities import AsyncAiClient, AiSettings
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))
        from test_files_api import create_async_test_client
        
        client = create_async_test_client()
        response = await client.ask("Analyze document file-123")
        assert len(response) > 0
    
    async def _test_async_error_handling(self):
        from ai_utilities import AsyncAiClient, AiSettings
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))
        from test_files_api import create_async_test_client
        from ai_utilities.providers.provider_exceptions import FileTransferError
        
        client = create_async_test_client()
        try:
            await client.download_file("nonexistent-file")
            assert False, "Should have raised exception"
        except FileTransferError:
            pass  # Expected
    
    def print_dashboard(self) -> None:
        """Print the complete test dashboard."""
        print("📊 TEST EXECUTION SUMMARY:")
        self._print_test_summary_table()
        print()
        
        print("🎯 AI MODULE SUPPORT MATRIX:")
        self._generate_module_support_matrix()
        print()
        
        print("🔍 DETAILED TEST BREAKDOWN:")
        for result in self.test_results:
            status = "✅" if result.failed == 0 else "❌"
            print(f"{result.category:<25}: {result.passed:>3}/{result.total:<3} {status}")
        print()
        
        # Show grand total prominently
        total_tests = sum(r.total for r in self.test_results)
        total_passed = sum(r.passed for r in self.test_results)
        total_failed = sum(r.failed for r in self.test_results)
        
        print(f"🎯 **GRAND TOTAL: {total_passed}/{total_tests} tests executed**")
        if total_failed > 0:
            print(f"⚠️  {total_failed} test failures detected")
        else:
            print("✅ All tests passed!")
        print()
        
        # Production readiness assessment
        if total_failed == 0:
            print("🚀 PRODUCTION READINESS: ✅ READY FOR MERGE")
        else:
            print("🚨 PRODUCTION READINESS: ❌ NEEDS FIXES")
        
        print(f"\n⏱️  Completed in: {(datetime.now() - self.start_time).total_seconds():.2f}s")
    
    def _print_test_summary_table(self):
        """Print the test summary table."""
        print("┌─────────────────────┬──────────┬──────────┬─────────────┐")
        print("│ Category            │ Total    │ Passed   │ Failed      │")
        print("├─────────────────────┼──────────┼──────────┼─────────────┤")
        
        for result in self.test_results:
            failed_str = f"{result.failed:9d}" if result.failed > 0 else "           0"
            print(f"│ {result.category[:19]:19} │ {result.total:8d} │ {result.passed:8d} │ {failed_str} │")
        
        print("├─────────────────────┼──────────┼──────────┼─────────────┤")
        
        # Calculate totals
        total_tests = sum(r.total for r in self.test_results)
        total_passed = sum(r.passed for r in self.test_results)
        total_failed = sum(r.failed for r in self.test_results)
        
        failed_str = f"{total_failed:9d}" if total_failed > 0 else "           0"
        print(f"│ {'TOTAL':19} │ {total_tests:8d} │ {total_passed:8d} │ {failed_str} │")
        print("└─────────────────────┴──────────┴──────────┴─────────────┘")
    
    def save_report(self, filename: str = None) -> None:
        """Save dashboard report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            # Redirect stdout to file
            import contextlib
            import io
            
            f.write(f"AI Utilities Test Report\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            # Write test results
            for result in self.test_results:
                f.write(f"{result.category}: {result.passed}/{result.total} passed\n")
            
            f.write(f"\nOverall: {sum(r.passed for r in self.test_results)}/{sum(r.total for r in self.test_results)} passed\n")
        
        print(f"📄 Report saved to: {filename}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="AI Utilities Test Dashboard")
    parser.add_argument("--verbose", action="store_true", help="Show detailed test output")
    parser.add_argument("--save-report", action="store_true", help="Save report to file")
    parser.add_argument("--integration", action="store_true", help="Run integration tests (requires API key)")
    parser.add_argument("--full-suite", action="store_true", help="Run complete test suite (including legacy/demo tests)")
    
    args = parser.parse_args()
    
    dashboard = TestDashboard()
    
    try:
        dashboard.run_tests(
            include_integration=args.integration,
            verbose=args.verbose,
            full_suite=args.full_suite
        )
        dashboard.print_dashboard()
        
        if args.save_report:
            dashboard.save_report()
        
        # Exit with appropriate code
        total_failed = sum(r.failed for r in dashboard.test_results)
        sys.exit(0 if total_failed == 0 else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Dashboard error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
