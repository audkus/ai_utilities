"""Advanced metrics collection examples for production monitoring scenarios."""

import asyncio
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

# === BOOTSTRAP: Ensure ai_utilities is importable from any location ===
script_path = Path(__file__).resolve()
repo_root = script_path.parent.parent.parent

# Add src directory to sys.path if not already there
src_dir = repo_root / "src"
src_dir_str = str(src_dir)
if src_dir_str not in sys.path:
    sys.path.insert(0, src_dir_str)

# Add repo root to sys.path for examples import
repo_root_str = str(repo_root)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)

from examples._common import print_header, output_dir, require_env
# === END BOOTSTRAP ===

from ai_utilities.metrics import MetricsCollector, PrometheusExporter, JSONExporter, OpenTelemetryExporter
from ai_utilities import AsyncAiClient


class ApplicationMetrics:
    """Example class showing how to integrate metrics into an application."""
    
    def __init__(self):
        self.collector = MetricsCollector()
        self.start_time = time.time()
        
        # Initialize application metrics
        self.request_counter = self.collector.create_counter(
            "requests_total",
            "Total number of requests processed",
            ["method", "endpoint"]
        )
        
        self.request_duration = self.collector.create_histogram(
            "request_duration_seconds",
            "Request processing duration",
            ["method", "endpoint"],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        self.active_connections = self.collector.create_gauge(
            "active_connections",
            "Number of active connections"
        )
        
        self.error_rate = self.collector.create_gauge(
            "error_rate",
            "Current error rate"
        )
    
    def record_request(self, method: str, endpoint: str, duration: float, success: bool):
        """Record a request with metrics."""
        self.request_counter.labels(method=method, endpoint=endpoint).inc()
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)
        
        if not success:
            self.error_rate.inc()
    
    def set_active_connections(self, count: int):
        """Set the number of active connections."""
        self.active_connections.set(count)
    
    def get_metrics_summary(self):
        """Get a summary of all metrics."""
        return {
            "uptime_seconds": time.time() - self.start_time,
            "total_requests": sum(self.request_counter.collect()),
            "avg_request_duration": sum(self.request_duration.collect()) / max(1, len(self.request_duration.collect())),
            "current_connections": self.active_connections._value.get(),
            "current_error_rate": self.error_rate._value.get()
        }


def main():
    """Demonstrate advanced metrics collection."""
    
    print_header("📊 Advanced Metrics Monitoring Demo")
    
    # Check for required environment variables
    if not require_env(['OPENAI_API_KEY']):
        print("❌ CONFIGURATION REQUIRED - Cannot proceed without API key")
        return 1
    
    # Initialize metrics
    print("\n🔧 Initializing metrics system...")
    try:
        metrics = ApplicationMetrics()
        print("✅ Metrics system initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize metrics: {e}")
        return 1
    
    # Simulate application activity
    print("\n🎯 Simulating Application Activity")
    print("-" * 40)
    
    try:
        # Simulate some requests
        endpoints = ["/api/users", "/api/posts", "/api/comments"]
        methods = ["GET", "POST", "PUT", "DELETE"]
        
        print("   Simulating API requests...")
        for i in range(10):
            import random
            method = random.choice(methods)
            endpoint = random.choice(endpoints)
            duration = random.uniform(0.1, 2.0)
            success = random.random() > 0.1  # 90% success rate
            
            metrics.record_request(method, endpoint, duration, success)
            metrics.set_active_connections(random.randint(1, 10))
            
            if i % 3 == 0:
                print(f"   Request {i+1}: {method} {endpoint} ({duration:.2f}s) - {'✅' if success else '❌'}")
        
        print("✅ Activity simulation complete!")
        
    except Exception as e:
        print(f"❌ Activity simulation failed: {e}")
        return 1
    
    # Export metrics in different formats
    print("\n🎯 Exporting Metrics")
    print("-" * 40)
    
    try:
        script_output_dir = output_dir(Path(__file__))
        
        # JSON Export
        print("   Exporting to JSON...")
        json_exporter = JSONExporter()
        json_metrics = json_exporter.export(metrics.collector)
        
        json_file = script_output_dir / "metrics.json"
        json_file.write_text(json_metrics, encoding='utf-8')
        print(f"✅ JSON metrics saved to: {json_file}")
        
        # Prometheus Export
        print("   Exporting to Prometheus format...")
        prometheus_exporter = PrometheusExporter()
        prometheus_metrics = prometheus_exporter.export(metrics.collector)
        
        prometheus_file = script_output_dir / "metrics.prom"
        prometheus_file.write_text(prometheus_metrics, encoding='utf-8')
        print(f"✅ Prometheus metrics saved to: {prometheus_file}")
        
        # Show metrics summary
        summary = metrics.get_metrics_summary()
        print(f"\n📊 Metrics Summary:")
        print(f"   Uptime: {summary['uptime_seconds']:.1f} seconds")
        print(f"   Total requests: {summary['total_requests']}")
        print(f"   Avg duration: {summary['avg_request_duration']:.2f} seconds")
        print(f"   Active connections: {summary['current_connections']}")
        print(f"   Error rate: {summary['current_error_rate']}")
        
        # Show preview of Prometheus metrics
        preview_lines = prometheus_metrics.splitlines()[:8]
        print(f"\n📝 Prometheus Metrics Preview:")
        for i, line in enumerate(preview_lines, 1):
            print(f"   {i}: {line[:80]}{'...' if len(line) > 80 else ''}")
        
    except Exception as e:
        print(f"❌ Metrics export failed: {e}")
        return 1
    
    # Async metrics collection demo
    print("\n🎯 Async Metrics Collection")
    print("-" * 40)
    
    try:
        async def async_metrics_demo():
            """Demonstrate async metrics collection."""
            print("   Starting async metrics collection...")
            
            # Simulate async operations
            async def simulate_async_request():
                await asyncio.sleep(0.1)
                metrics.record_request("GET", "/async/endpoint", 0.1, True)
                return "success"
            
            # Run multiple async requests
            tasks = [simulate_async_request() for _ in range(5)]
            results = await asyncio.gather(*tasks)
            
            print(f"   Completed {len(results)} async requests")
            return len(results)
        
        # Run async demo
        async_count = asyncio.run(async_metrics_demo())
        print(f"✅ Async demo complete: {async_count} requests")
        
    except Exception as e:
        print(f"❌ Async demo failed: {e}")
        return 1
    
    print(f"\n🎉 Advanced metrics monitoring demo complete!")
    
    # Show output directory
    script_output_dir = output_dir(Path(__file__))
    print(f"\n📁 All outputs saved to: {script_output_dir}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        print("\n💡 Need help? Check the documentation or run with proper configuration")
    exit(exit_code)
