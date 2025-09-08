import time
import threading
from typing import Optional
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, HTTPException, Query, Request
from starlette.responses import JSONResponse, HTMLResponse
import uvicorn
from metrics import MetricsStore
from pathlib import Path


WATCH_DIR = Path("watch_dir")
UNPROCESSED = WATCH_DIR / "unprocessed"
UNDERPROCESS = WATCH_DIR / "underprocess"
PROCESSED = WATCH_DIR / "processed"

class DashboardServer:
    """FastAPI-based dashboard server for DAG pipeline observability."""
    
    def __init__(self, metrics_store: Optional[MetricsStore] = None):
        self.app = FastAPI(
            title="DAG Pipeline Dashboard", 
            version="1.0.0",
            description="Real-time observability for DAG-based line processing pipeline"
        )
        self.metrics_store = metrics_store or MetricsStore.get_instance()
        self.templates = Jinja2Templates(directory="templates")
        self.setup_routes()
    
    def setup_routes(self):
        """Configure all API routes."""
        
        @self.app.get("/")
        async def root():
            """Root endpoint with API information."""
            return {
                "service": "DAG Pipeline Dashboard",
                "version": "1.0.0",
                "description": "Real-time observability dashboard",
                "endpoints": {
                    "stats": "/stats - Processor statistics with memory metrics",
                    "trace": "/trace - Enhanced line traces with search and filtering",
                    "errors": "/errors - Recent error logs",
                    "processors": "/processors - List all processors with status",
                    "health": "/health - Service health check with memory stats",
                    "dashboard": "/dashboard - HTML dashboard"
                },
                "trace_enabled": self.metrics_store.trace_enabled,
                "timestamp": time.time()
            }
        
        @self.app.get("/stats")
        async def get_stats():
            """Get current processor statistics with memory + file queue metrics."""
            try:
                stats = self.metrics_store.get_stats()
                memory_stats = self.metrics_store.get_memory_stats()
                
                total_lines = sum(p.get("count", 0) for p in stats.values())
                total_errors = sum(p.get("errors", 0) for p in stats.values())
                total_time = sum(p.get("total_time", 0.0) for p in stats.values())
                
                # File queue info
                file_stats = self.metrics_store.get_file_stats(last_n=10)
                file_queue = {
                    "unprocessed": len(list(UNPROCESSED.glob("*"))),
                    "underprocess": len(list(UNDERPROCESS.glob("*"))),
                    "processed": len(list(PROCESSED.glob("*"))),
                    "current_file": file_stats.get("current_file"),
                    "last_processed": file_stats.get("last_processed", [])
                }
                
                return JSONResponse(content={
                    "timestamp": time.time(),
                    "processors": stats,
                    "memory": memory_stats,
                    "summary": {
                        "total_processors": len(stats),
                        "total_lines_processed": total_lines,
                        "total_errors": total_errors,
                        "total_processing_time": round(total_time, 4),
                        "avg_processing_time": round(total_time / max(total_lines, 1), 6),
                        "memory_usage_mb": memory_stats.get("current_memory_mb", 0),
                        "memory_growth_mb": memory_stats.get("memory_growth_mb", 0)
                    },
                    "file_queue": file_queue
                })
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")

        
        @self.app.get("/trace")
        async def get_trace(
            limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of traces to return"),
            search: str = Query(default="", description="Search in trace content"),
            processor: str = Query(default="", description="Filter by processor name"),
            tag: str = Query(default="", description="Filter by output tag")
        ):
            """Get recent line traces with enhanced search and filtering."""
            try:
                traces = self.metrics_store.get_traces(
                    limit=limit, 
                    search=search, 
                    processor_filter=processor,
                    tag_filter=tag
                )
                
                return JSONResponse(content={
                    "timestamp": time.time(),
                    "traces": traces,
                    "total_traces": len(traces),
                    "trace_enabled": self.metrics_store.trace_enabled,
                    "filters": {
                        "limit": limit,
                        "search": search,
                        "processor": processor,
                        "tag": tag
                    }
                })
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error retrieving traces: {str(e)}")
        
        @self.app.get("/errors")
        async def get_errors(
            limit: int = Query(default=50, ge=1, le=500, description="Maximum number of errors to return")
        ):
            """Get recent errors."""
            try:
                errors = self.metrics_store.get_errors(limit=limit)
                return JSONResponse(content={
                    "timestamp": time.time(),
                    "errors": errors,
                    "total_errors": len(errors),
                    "limit": limit
                })
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error retrieving errors: {str(e)}")
        
        @self.app.get("/processors")
        async def get_processors():
            """Get list of all processors with their status and basic metrics."""
            try:
                processors = self.metrics_store.get_processors()
                stats = self.metrics_store.get_stats()
                
                # Enrich processor data with detailed metrics
                enriched_processors = []
                for proc in processors:
                    proc_name = proc["name"]
                    if proc_name in stats:
                        detailed_metrics = stats[proc_name]
                        proc.update({
                            "total_time": detailed_metrics.get("total_time", 0.0),
                            "memory_usage_mb": detailed_metrics.get("memory_usage_mb", 0.0)
                        })
                    enriched_processors.append(proc)
                
                return JSONResponse(content={
                    "timestamp": time.time(),
                    "processors": enriched_processors,
                    "total_processors": len(enriched_processors),
                    "active_processors": len([p for p in enriched_processors if p["status"] == "active"]),
                    "idle_processors": len([p for p in enriched_processors if p["status"] == "idle"])
                })
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error retrieving processors: {str(e)}")
        
        @self.app.get("/health")
        async def health_check():
            """Enhanced health check endpoint with memory statistics."""
            try:
                stats = self.metrics_store.get_stats()
                memory_stats = self.metrics_store.get_memory_stats()
                
                return {
                    "status": "healthy",
                    "timestamp": time.time(),
                    "trace_enabled": self.metrics_store.trace_enabled,
                    "active_processors": len(stats),
                    "uptime_seconds": time.time() - getattr(self, '_start_time', time.time()),
                    "memory": memory_stats,
                    "system_health": {
                        "memory_usage_ok": memory_stats.get("memory_percent", 0) < 90,
                        "active_traces": len(self.metrics_store._active_traces) if hasattr(self.metrics_store, '_active_traces') else 0,
                        "stored_traces": len(self.metrics_store.traces),
                        "stored_errors": len(self.metrics_store.errors)
                    }
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error in health check: {str(e)}")
        
        @self.app.get("/dashboard", response_class=HTMLResponse)
        async def get_dashboard(request: Request):
            return self.templates.TemplateResponse("dashboard.html", {"request": request})
    
    def start(self, host: str = "0.0.0.0", port: int = 8000) -> threading.Thread:
        """Start the dashboard server in a background thread."""
        self._start_time = time.time()
        
        def run_server():
            uvicorn.run(
                self.app,
                host=host,
                port=port,
                log_level="error",
                access_log=False
            )
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # Give server a moment to start
        time.sleep(0.5)
        
        return self.server_thread
    
    def is_running(self) -> bool:
        """Check if the dashboard server is running."""
        return hasattr(self, 'server_thread') and self.server_thread is not None and self.server_thread.is_alive()

# Convenience functions for backwards compatibility
def create_dashboard(metrics_store: Optional[MetricsStore] = None) -> DashboardServer:
    """Create a new dashboard server instance."""
    return DashboardServer(metrics_store)

def start_dashboard(port: int = 8000, metrics_store: Optional[MetricsStore] = None) -> threading.Thread:
    """Start dashboard server and return the thread."""
    dashboard = DashboardServer(metrics_store)
    return dashboard.start(port=port)
