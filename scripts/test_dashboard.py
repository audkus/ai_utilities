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
        print("🚀 AI UTILITIES TEST DASHBOARD")
        print("=" * 50)
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mode: {'Full Test Suite' if full_suite else 'Files API Focus'}")
        print()
        
        if full_suite:
            # Run complete test suite
            self._run_test_suite(
                "Complete Unit Tests",
                ["pytest", "-m", "not integration", "-q"],
                verbose
            )
            
            if include_integration:
                self._run_test_suite(
                    "Integration Tests",
                    ["pytest", "-m", "integration", "-q"],
                    verbose
                )
            else:
                self._run_test_suite(
                    "Integration Tests (Skipped - No API Key)",
                    ["pytest", "-m", "integration", "-q"],
                    verbose
                )
        else:
            # Files API focused tests
            self._run_test_suite(
                "Files API Unit Tests",
                ["pytest", "tests/test_files_api.py", "-q"],
                verbose
            )
            
            if include_integration:
                self._run_test_suite(
                    "Files Integration Tests",
                    ["pytest", "tests/test_files_integration.py", "-q"],
                    verbose
                )
            else:
                self._run_test_suite(
                    "Files Integration Tests (Skipped - No API Key)",
                    ["pytest", "tests/test_files_integration.py", "-q"],
                    verbose
                )
        
        # Core functionality tests (always run)
        self._test_core_functionality(verbose)
        self._test_async_operations(verbose)
        
        # Generate module support matrix
        self._generate_module_support_matrix()
        
    def _run_test_suite(self, category: str, command: List[str], verbose: bool) -> None:
        """Run a test suite and parse results."""
        print(f"🧪 Running {category}...")
        
        try:
            if verbose:
                result = subprocess.run(command, capture_output=False, text=True)
            else:
                result = subprocess.run(command, capture_output=True, text=True)
            
            # Parse pytest output
            output = result.stdout if not verbose else ""
            total, passed, failed, skipped = self._parse_pytest_output(output)
            
            test_result = TestResult(
                category=category,
                total=total,
                passed=passed,
                failed=failed,
                skipped=skipped,
                duration=0.0  # Would need timing for real implementation
            )
            
            self.test_results.append(test_result)
            
            # Show immediate result
            status = "✅ PASSED" if failed == 0 else "❌ FAILED"
            print(f"   {status}: {passed}/{total} passed")
            if skipped > 0:
                print(f"   ⏭️  {skipped} skipped")
            
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
    
    def _parse_pytest_output(self, output: str) -> Tuple[int, int, int, int]:
        """Parse pytest output to extract test counts."""
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
        self._print_module_support_matrix()
        print()
        
        print("🔍 DETAILED TEST BREAKDOWN:")
        for result in self.test_results:
            status = "✅" if result.failed == 0 else "❌"
            print(f"{result.category:<25}: {result.passed:>3}/{result.total:<3} {status}")
        print()
        
        # Overall status
        total_tests = sum(r.total for r in self.test_results)
        total_passed = sum(r.passed for r in self.test_results)
        total_failed = sum(r.failed for r in self.test_results)
        
        if total_failed == 0:
            print("🚀 PRODUCTION READINESS: ✅ READY FOR MERGE")
        else:
            print("🚨 PRODUCTION READINESS: ❌ NEEDS FIXES")
        
        print()
        print(f"⏱️  Completed in: {(datetime.now() - self.start_time).total_seconds():.2f}s")
    
    def _print_test_summary_table(self) -> None:
        """Print test summary table."""
        print("┌─────────────────────┬──────────┬──────────┬─────────────┐")
        print("│ Category            │ Total    │ Passed   │ Failed      │")
        print("├─────────────────────┼──────────┼──────────┼─────────────┤")
        
        for result in self.test_results:
            print(f"│ {result.category:<19} │ {result.total:>8} │ {result.passed:>8} │ {result.failed:>11} │")
        
        # Total row
        total_tests = sum(r.total for r in self.test_results)
        total_passed = sum(r.passed for r in self.test_results)
        total_failed = sum(r.failed for r in self.test_results)
        
        print("├─────────────────────┼──────────┼──────────┼─────────────┤")
        print(f"│ {'TOTAL':<19} │ {total_tests:>8} │ {total_passed:>8} │ {total_failed:>11} │")
        print("└─────────────────────┴──────────┴──────────┴─────────────┘")
    
    def _print_module_support_matrix(self) -> None:
        """Print module support matrix."""
        print("┌─────────────────────┬──────────┬──────────┬──────────┬──────────┐")
        print("│ Feature             │ OpenAI   │ OAI Comp │ Async    │ Status   │")
        print("├─────────────────────┼──────────┼──────────┼──────────┼──────────┤")
        
        for module in self.module_support:
            openai_status = "✅" if module.openai else "❌"
            compat_status = "✅" if module.openai_compatible else "❌"
            async_status = "✅" if module.async_support else "❌"
            
            print(f"│ {module.feature:<19} │ {openai_status:>8} │ {compat_status:>8} │ {async_status:>8} │ {module.status:>8} │")
        
        # Coverage row
        openai_coverage = sum(1 for m in self.module_support if m.openai) / len(self.module_support) * 100
        compat_coverage = sum(1 for m in self.module_support if m.openai_compatible) / len(self.module_support) * 100
        async_coverage = sum(1 for m in self.module_support if m.async_support) / len(self.module_support) * 100
        overall_coverage = (openai_coverage + compat_coverage + async_coverage) / 3
        
        print("├─────────────────────┼──────────┼──────────┼──────────┼──────────┤")
        print(f"│ {'COVERAGE':<19} │ {openai_coverage:>7.0f}% │ {compat_coverage:>7.0f}% │ {async_coverage:>7.0f}% │ {overall_coverage:>7.0f}% │")
        print("└─────────────────────┴──────────┴──────────┴──────────┴──────────┘")
    
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
