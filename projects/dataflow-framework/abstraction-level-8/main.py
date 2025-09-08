import os
import threading
import time
import uvicorn
from fastapi import FastAPI
from starlette.responses import JSONResponse
from typing import Iterator, Optional
from pipeline import build_routing, run_router
from metrics import MetricsStore

def read_lines(path: str) -> Iterator[str]:
    """Read lines from a file, stripping newlines."""
    with open(path, "r") as file:
        for line in file:
            yield line.rstrip("\n")

def write_output(lines: Iterator[str], output_file: Optional[str]) -> None:
    """Write lines to a file or print to console if output_file is None."""
    if output_file is None:
        for line in lines:
            print(line)
    else:
        output_file = os.path.abspath(os.path.expanduser(output_file))
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w") as file:
            for line in lines:
                file.write(line + "\n")

def start_dashboard_server(port: int = 8000) -> threading.Thread:
    """Start FastAPI dashboard server in a background thread."""
    
    app = FastAPI(title="DAG Pipeline Dashboard", version="1.0.0")
    metrics_store = MetricsStore.get_instance()
    
    @app.get("/")
    async def root():
        """Root endpoint with basic info."""
        return {
            "message": "DAG Pipeline Dashboard", 
            "version": "1.0.0",
            "endpoints": ["/stats", "/trace", "/errors"]
        }
    
    @app.get("/stats")
    async def get_stats():
        """Get current processor statistics."""
        stats = metrics_store.get_stats()
        return JSONResponse(content={
            "timestamp": time.time(),
            "processors": stats,
            "summary": {
                "total_processors": len(stats),
                "total_lines_processed": sum(p.get("count", 0) for p in stats.values()),
                "total_errors": sum(p.get("errors", 0) for p in stats.values())
            }
        })
    
    @app.get("/trace")
    async def get_trace(limit: int = 100):
        """Get recent line traces."""
        traces = metrics_store.get_traces(limit=limit)
        return JSONResponse(content={
            "timestamp": time.time(),
            "traces": traces,
            "total_traces": len(traces),
            "trace_enabled": metrics_store.trace_enabled
        })
    
    @app.get("/errors")
    async def get_errors(limit: int = 50):
        """Get recent errors."""
        errors = metrics_store.get_errors(limit=limit)
        return JSONResponse(content={
            "timestamp": time.time(),
            "errors": errors,
            "total_errors": len(errors)
        })
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "timestamp": time.time()}
    
    def run_server():
        """Run the FastAPI server with minimal logging."""
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=port, 
            log_level="error",  # Minimize uvicorn logs
            access_log=False    # Disable access logs
        )
    
    # Start server in daemon thread
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    
    # Give server a moment to start
    time.sleep(0.5)
    return thread


def run(
    input_path: str, 
    config_path: str, 
    output_path: Optional[str],
    trace_enabled: bool = False,
    dashboard_enabled: bool = True,
    dashboard_port: int = 8000,
    max_traces: int = 1000,
    max_errors: int = 100
) -> None:
    """Run the tag-based routing engine on input lines with observability."""
    
    # Initialize metrics store with configuration
    metrics_store = MetricsStore.get_instance(max_traces=max_traces, max_errors=max_errors)
    metrics_store.set_trace_enabled(trace_enabled)
    
    # Start dashboard if enabled - CORRECTED VERSION
    dashboard_server = None
    if dashboard_enabled:
        try:
            from dashboard import DashboardServer
            dashboard_server = DashboardServer(metrics_store)  # Pass metrics_store explicitly
            dashboard_thread = dashboard_server.start(port=dashboard_port)
            print(f"Dashboard started at http://localhost:{dashboard_port}")
            print(f"   • Stats: http://localhost:{dashboard_port}/stats")
            print(f"   • Dashboard: http://localhost:{dashboard_port}/dashboard")
            print(f"   • Traces: http://localhost:{dashboard_port}/trace")
            print(f"   • Errors: http://localhost:{dashboard_port}/errors")
            print()
        except Exception as e:
            print(f"Warning: Could not start dashboard: {e}")
            print("Pipeline will continue without dashboard")
            dashboard_enabled = False
    
    # Record pipeline start time
    pipeline_start = time.time()
    
    try:
        # Read input lines
        print(f"Reading lines from: {input_path}")
        lines = read_lines(input_path)
        
        # Build routing configuration
        print(f"Building routing from: {config_path}")
        nodes = build_routing(config_path)
        
        # Load start tag from config
        import yaml
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f)
        start_tag = cfg.get("start", "start")
        
        print(f"Starting pipeline at tag: {start_tag}")
        if trace_enabled:
            print(f"Tracing enabled (storing {max_traces} traces)")
        
        # Run the router
        output_lines = run_router(start_tag, lines, nodes)
        
        # Write output
        if output_path:
            print(f"Writing output to: {output_path}")
        else:
            print("Writing output to console")
        
        write_output(output_lines, output_path)
        
    except Exception as e:
        # Record pipeline-level error
        metrics_store.record_error("pipeline", e, None)
        print(f"Pipeline error: {e}")
        raise
    
    finally:
        # Report final statistics
        pipeline_duration = time.time() - pipeline_start
        stats = metrics_store.get_stats()
        
        print("\n" + "=" * 60)
        print("PIPELINE SUMMARY")
        print("=" * 60)
        print(f"Total time: {pipeline_duration:.2f}s")
        
        if stats:
            total_lines = sum(p.get("count", 0) for p in stats.values())
            total_errors = sum(p.get("errors", 0) for p in stats.values())
            print(f"Lines processed: {total_lines}")
            print(f"Total errors: {total_errors}")
            
            print("\nProcessor Statistics:")
            for processor, metrics in stats.items():
                count = metrics.get("count", 0)
                avg_time = metrics.get("avg_time", 0.0)
                errors = metrics.get("errors", 0)
                print(f"  • {processor}: {count} lines, {avg_time:.4f}s avg, {errors} errors")
        
        if dashboard_enabled and dashboard_server:
            print(f"\nDashboard running at http://localhost:{dashboard_port}/dashboard")
            print("Press Ctrl+C to stop")
            
            # Keep dashboard alive
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down...")

# Legacy function signature for backwards compatibility
def run_legacy(input_path: str, config_path: str, output_path: Optional[str]) -> None:
    """Legacy run function for backwards compatibility."""
    run(input_path, config_path, output_path)
