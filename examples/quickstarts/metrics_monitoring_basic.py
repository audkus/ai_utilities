"""Example demonstrating comprehensive metrics collection and monitoring in ai_utilities."""

import json
import time
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

from examples._common import print_header, output_dir, safe_write_bytes
# === END BOOTSTRAP ===

from ai_utilities.metrics import MetricsCollector, PrometheusExporter, JSONExporter
from ai_utilities import AiClient


def demonstrate_basic_metrics():
    """Demonstrate basic metrics collection functionality."""
    
    print_header("Basic Metrics Collection")
    
    # Create a metrics collector
    collector = MetricsCollector()
    
    # Record different types of metrics
    print("1. Recording different metric types...")
    
    # Counter metrics (incrementing values)
    collector.increment_counter("api_requests", labels={"provider": "openai"})
    collector.increment_counter("api_requests", labels={"provider": "openai"})
    collector.increment_counter("api_requests", labels={"provider": "groq"})
    
    # Gauge metrics (current values)
    collector.set_gauge("active_connections", 5, labels={"service": "ai-api"})
    collector.set_gauge("memory_usage", 1024, labels={"component": "collector"})
    
    # Histogram metrics (value distributions)
    collector.observe_histogram("response_time", 0.5, labels={"endpoint": "/chat"})
    collector.observe_histogram("response_time", 1.2, labels={"endpoint": "/chat"})
    collector.observe_histogram("response_time", 2.1, labels={"endpoint": "/chat"})
    
    # Timer metrics (duration tracking)
    collector.record_timer("request_latency", 0.8, labels={"model": "gpt-4"})
    collector.record_timer("request_latency", 1.1, labels={"model": "gpt-4"})
    collector.record_timer("request_latency", 0.6, labels={"model": "gpt-3.5-turbo"})
    
    print("✓ Metrics recorded successfully")
    
    # Get all metrics
    all_metrics = collector.get_all_metrics()
    print(f"\n2. Total metrics collected: {len(all_metrics)}")
    
    # Display metrics by type
    print("\n3. Metrics by type:")
    for metric in all_metrics[:10]:  # Show first 10 for brevity
        print(f"   {metric.name}: {metric.value} ({metric.metric_type.name})")
    
    if len(all_metrics) > 10:
        print(f"   ... and {len(all_metrics) - 10} more")
    
    return collector


def demonstrate_timer_snapshots():
    """Demonstrate timer snapshot metrics."""
    
    print_header("Timer Snapshot Metrics")
    
    collector = MetricsCollector()
    
    # Simulate API request latency tracking
    print("1. Simulating API request latencies...")
    
    latencies = [0.8, 1.2, 0.5, 2.1, 0.9, 1.5, 0.7, 1.8]
    
    for i, latency in enumerate(latencies, 1):
        collector.record_timer("api_latency", latency, labels={"endpoint": "/chat"})
        print(f"   Request {i}: {latency}s")
    
    # Get timer snapshot metrics
    all_metrics = collector.get_all_metrics()
    timer_metrics = {m.name: m.value for m in all_metrics if "api_latency" in m.name}
    
    print(f"\n2. Timer snapshot metrics ({len(timer_metrics)} total):")
    
    # Show the 5 timer snapshot metrics
    snapshot_metrics = [
        ("api_latency_count", "Total requests"),
        ("api_latency_sum_seconds", "Total time (s)"),
        ("api_latency_min_seconds", "Min latency (s)"),
        ("api_latency_max_seconds", "Max latency (s)"),
        ("api_latency_last_seconds", "Last latency (s)")
    ]
    
    for metric_name, description in snapshot_metrics:
        if metric_name in timer_metrics:
            print(f"   {description}: {timer_metrics[metric_name]}")
    
    return collector


def demonstrate_context_manager():
    """Demonstrate timer context manager for automatic timing."""
    
    print_header("Timer Context Manager")
    
    collector = MetricsCollector()
    
    print("1. Using context manager for automatic timing...")
    
    # Simulate different operations with automatic timing
    operations = [
        ("database_query", {"table": "users"}, 0.1),
        ("api_call", {"endpoint": "/chat"}, 0.5),
        ("file_processing", {"type": "csv"}, 0.8),
        ("cache_lookup", {"key": "user:123"}, 0.01)
    ]
    
    for operation_name, labels, simulated_duration in operations:
        print(f"   Simulating {operation_name}...")
        
        # In real usage, the context manager automatically times the code
        with collector.timer(operation_name, labels=labels):
            # Simulate work with sleep
            time.sleep(simulated_duration)
        
        print(f"   ✓ {operation_name} completed")
    
    # Show the results
    all_metrics = collector.get_all_metrics()
    operation_metrics = {m.name: m.value for m in all_metrics if any(op in m.name for op, _, _ in operations)}
    
    print(f"\n2. Operation timing results:")
    for metric_name, value in operation_metrics.items():
        if "_seconds" in metric_name:
            op_name = metric_name.replace("_last_seconds", "")
            print(f"   {op_name}: {value:.3f}s")
    
    return collector


def demonstrate_exporters():
    """Demonstrate metrics export to different formats."""
    
    print_header("Metrics Exporters")
    
    # Create a collector with some sample data
    collector = MetricsCollector()
    
    # Add sample metrics
    collector.increment_counter("requests_total", labels={"method": "POST"})
    collector.set_gauge("active_users", 42)
    collector.record_timer("response_time", 1.5, labels={"endpoint": "/api"})
    
    print("1. Prometheus Export Format:")
    prometheus_exporter = PrometheusExporter(collector)
    prometheus_output = prometheus_exporter.export()
    
    # Show first few lines of Prometheus output
    prometheus_lines = prometheus_output.split('\n')[:15]
    for line in prometheus_lines:
        if line.strip():
            print(f"   {line}")
    if len(prometheus_output.split('\n')) > 15:
        print("   ...")
    
    print(f"\n2. JSON Export Format:")
    json_exporter = JSONExporter(collector)
    json_output = json_exporter.export()
    
    # Parse and show JSON structure
    json_data = json.loads(json_output)
    
    print(f"   Total metrics in JSON: {len(json_data)}")
    print("   Sample metrics:")
    for metric in json_data[:3]:
        print(f"   - {metric['name']}: {metric['value']} ({metric['metric_type']})")
    
    # Save outputs
    script_output_dir = output_dir(Path(__file__))
    
    prometheus_file = script_output_dir / "metrics.prometheus"
    json_file = script_output_dir / "metrics.json"
    
    safe_write_bytes(prometheus_file, prometheus_output.encode('utf-8'))
    safe_write_bytes(json_file, json_output.encode('utf-8'))
    
    print(f"\n📁 Outputs saved to:")
    print(f"   Prometheus: {prometheus_file}")
    print(f"   JSON: {json_file}")
    
    return collector


def demonstrate_ai_client_integration():
    """Demonstrate metrics collection with AI client usage."""
    
    print_header("AI Client Integration")
    
    # Set up metrics collection
    collector = MetricsCollector()
    
    print("1. Setting up AI client with metrics tracking...")
    
    # Note: This example shows the pattern - you'd need real API keys for actual usage
    try:
        client = AiClient()
        
        # Track AI client usage
        print("   Tracking AI client metrics...")
        
        # Simulate AI requests with metrics
        requests = [
            ("What is machine learning?", "gpt-4"),
            ("Explain quantum computing", "gpt-3.5-turbo"),
            ("How does caching work?", "gpt-4")
        ]
        
        for i, (prompt, model) in enumerate(requests, 1):
            print(f"   Request {i}: {prompt[:30]}...")
            
            # Track request start
            start_time = time.time()
            
            try:
                # In real usage, this would make an actual API call
                # response = client.ask(prompt, model=model)
                
                # Simulate API call time
                time.sleep(0.1)  # Simulate network latency
                
                # Track successful request
                collector.increment_counter("ai_requests", labels={"model": model, "status": "success"})
                
                # Track response time
                response_time = time.time() - start_time
                collector.record_timer("ai_response_time", response_time, labels={"model": model})
                
                print(f"     ✓ Success ({response_time:.2f}s")
                
            except Exception as e:
                # Track failed request
                collector.increment_counter("ai_requests", labels={"model": model, "status": "error"})
                print(f"     ✗ Error: {e}")
        
        # Show AI client metrics
        all_metrics = collector.get_all_metrics()
        ai_metrics = {m.name: m.value for m in all_metrics if "ai_" in m.name}
        
        print(f"\n2. AI Client Metrics Summary:")
        print(f"   Total requests: {sum(v for k, v in ai_metrics.items() if 'ai_requests' in k)}")
        
        # Show response time stats
        response_time_metrics = {k: v for k, v in ai_metrics.items() if "ai_response_time" in k}
        if response_time_metrics:
            print(f"   Response time metrics: {len(response_time_metrics)}")
            for metric_name, value in list(response_time_metrics.items())[:3]:
                print(f"   - {metric_name}: {value:.3f}")
        
    except Exception as e:
        print(f"   Note: AI client integration requires proper setup. Error: {e}")
        print("   Configure API keys in .env file for full functionality.")
    
    return collector


def demonstrate_real_world_scenario():
    """Demonstrate a real-world monitoring scenario."""
    
    print_header("Real-World Monitoring Scenario")
    
    collector = MetricsCollector()
    
    print("1. Simulating web application with AI features...")
    
    # Simulate a web application with various operations
    operations = [
        ("user_login", 0.05, {"endpoint": "/login"}),
        ("ai_chat_query", 1.2, {"model": "gpt-4", "endpoint": "/chat"}),
        ("database_query", 0.15, {"table": "users", "query": "select"}),
        ("cache_hit", 0.01, {"cache": "redis"}),
        ("ai_image_generation", 3.5, {"model": "dall-e-3", "endpoint": "/generate"}),
        ("file_upload", 0.8, {"type": "image", "size": "large"}),
        ("ai_chat_query", 0.9, {"model": "gpt-3.5-turbo", "endpoint": "/chat"}),
        ("user_logout", 0.02, {"endpoint": "/logout"}),
    ]
    
    # Track system metrics
    collector.set_gauge("active_users", 127, labels={"service": "web"})
    collector.set_gauge("memory_usage", 512, labels={"component": "application"})
    
    # Process operations
    for i, (operation, duration, labels) in enumerate(operations, 1):
        print(f"   Processing operation {i}: {operation}")
        
        # Track operation count
        collector.increment_counter("operations_total", labels=labels)
        
        # Track operation timing
        with collector.timer(f"operation_duration", labels={"operation": operation}):
            time.sleep(min(duration, 0.1))  # Cap sleep for demo
        
        # Track specific operation types
        if "ai_" in operation:
            collector.record_timer(f"ai_operations", duration, labels=labels)
        
        print(f"     ✓ Completed")
    
    # Generate monitoring report
    print(f"\n2. Monitoring Report:")
    
    all_metrics = collector.get_all_metrics()
    
    # System health
    system_metrics = {m.name: m.value for m in all_metrics if m.name in ["active_users", "memory_usage"]}
    print(f"   System Health:")
    for name, value in system_metrics.items():
        print(f"   - {name}: {value}")
    
    # Operations summary
    operation_counts = {m.name: m.value for m in all_metrics if "operations_total" in m.name}
    total_ops = sum(operation_counts.values())
    print(f"   Total Operations: {total_ops}")
    
    # AI operations summary
    ai_metrics = {m.name: m.value for m in all_metrics if "ai_operations" in m.name}
    if ai_metrics:
        print(f"   AI Operations:")
        for name, value in list(ai_metrics.items())[:3]:
            print(f"   - {name}: {value:.3f}")
    
    # Export for monitoring systems
    print(f"\n3. Export for Monitoring Systems:")
    
    prometheus_exporter = PrometheusExporter(collector)
    json_exporter = JSONExporter(collector)
    
    prometheus_output = prometheus_exporter.export()
    json_output = json_exporter.export()
    
    print(f"   Prometheus metrics: {len(prometheus_output.split())} lines")
    print(f"   JSON metrics: {len(json.loads(json_output))} objects")
    
    # Save comprehensive report
    script_output_dir = output_dir(Path(__file__))
    
    report_file = script_output_dir / "monitoring_report.json"
    prometheus_file = script_output_dir / "monitoring.prometheus"
    
    safe_write_bytes(report_file, json_output.encode('utf-8'))
    safe_write_bytes(prometheus_file, prometheus_output.encode('utf-8'))
    
    print(f"\n📁 Monitoring report saved to: {report_file}")
    print(f"📁 Prometheus metrics saved to: {prometheus_file}")
    
    return collector


def main():
    """Run all metrics demonstration examples."""
    
    print_header("🔧 AI Utilities Metrics Collection Examples")
    
    # Run all demonstrations
    demonstrate_basic_metrics()
    demonstrate_timer_snapshots()
    demonstrate_context_manager()
    demonstrate_exporters()
    demonstrate_ai_client_integration()
    demonstrate_real_world_scenario()
    
    print(f"\n🎉 All metrics examples completed successfully!")
    print(f"\n📚 Next Steps:")
    print(f"   - Try the examples with your own AI API keys")
    print(f"   - Export metrics to your monitoring system")
    print(f"   - Integrate with your application's monitoring")
    print(f"   - Check out the documentation for advanced features")
    
    # Show output directory
    script_output_dir = output_dir(Path(__file__))
    print(f"\n📁 All outputs saved to: {script_output_dir}")


if __name__ == "__main__":
    main()
