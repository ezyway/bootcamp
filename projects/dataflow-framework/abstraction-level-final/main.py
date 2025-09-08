import os
import threading
import time
import uvicorn
import shutil
from pathlib import Path
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


# --- Folder queue utilities (Level 8) ---

def ensure_queue_dirs(watch_dir: str) -> dict:
    """Ensure watch_dir has unprocessed, underprocess, and processed folders.

    Returns a dict with Path objects for each folder.
    """
    base = Path(watch_dir).expanduser().resolve()
    unprocessed = base / "unprocessed"
    underprocess = base / "underprocess"
    processed = base / "processed"

    for p in (unprocessed, underprocess, processed):
        p.mkdir(parents=True, exist_ok=True)

    return {"base": base, "unprocessed": unprocessed, "underprocess": underprocess, "processed": processed}


def recover_underprocess(underprocess: Path, unprocessed: Path):
    """Move any files left in underprocess back to unprocessed (recovery on startup)."""
    for item in sorted(underprocess.iterdir()):
        if item.is_file():
            try:
                shutil.move(str(item), str(unprocessed / item.name))
                print(f"Recovered in-progress file back to unprocessed/: {item.name}")
            except Exception as e:
                print(f"Failed to recover {item}: {e}")


def atomic_move_to(src: Path, dest_dir: Path) -> Path:
    """Atomically move src into dest_dir and return new Path."""
    dest = dest_dir / src.name
    shutil.move(str(src), str(dest))
    return dest


def process_file(
    file_path: Path,
    config_path: str,
    metrics_store: MetricsStore,
    output_dir: Path,
):
    """Process a single file line-by-line through the routing engine.

    - Reads lines from file_path
    - Builds routing from config_path
    - Runs router and writes output to output_dir/<filename>.out
    - Updates metrics_store file tracking
    """
    filename = file_path.name
    metrics_store.set_current_file(filename)
    print(f"Processing file: {filename}")

    try:
        # Build routing (load processors)
        nodes = build_routing(config_path)

        # Read lines and run router
        lines = read_lines(str(file_path))

        # Load start tag from config
        import yaml
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f)
        start_tag = cfg.get("start", "start")

        output_lines = run_router(start_tag, lines, nodes)

        # Write outputs to processed/<filename>.out
        os.makedirs(output_dir, exist_ok=True)
        out_file = output_dir / (filename + ".out")
        write_output(output_lines, str(out_file))

        # Record processed file in metrics
        metrics_store.record_processed_file(filename)
        print(f"Finished processing: {filename}")
        return True

    except Exception as e:
        metrics_store.record_error("file_processor", e, str(file_path))
        print(f"Error processing {filename}: {e}")
        return False

    finally:
        metrics_store.set_current_file(None)


def monitor_folder(
    watch_dir: str,
    config_path: str,
    metrics_store: MetricsStore,
    poll_interval: float = 1.0,
    stop_event: threading.Event | None = None,
):
    """Continuously monitor watch_dir/unprocessed for new files and process them.

    Files are moved to underprocess/ while being worked on and then to processed/ when done.
    """
    paths = ensure_queue_dirs(watch_dir)
    unprocessed = paths["unprocessed"]
    underprocess = paths["underprocess"]
    processed = paths["processed"]

    # On startup, recover any in-progress files
    recover_underprocess(underprocess, unprocessed)

    print(f"Monitoring directory: {unprocessed} for new files...")

    stop_event = stop_event or threading.Event()

    while not stop_event.is_set():
        try:
            # list files in alphabetical/ctime order
            candidates = sorted([p for p in unprocessed.iterdir() if p.is_file()], key=lambda p: p.stat().st_mtime)
            if not candidates:
                time.sleep(poll_interval)
                continue

            for candidate in candidates:
                # Atomically move to underprocess to claim it
                try:
                    claimed = atomic_move_to(candidate, underprocess)
                except Exception as e:
                    print(f"Failed to claim file {candidate.name}: {e}")
                    continue

                # Process file
                ok = process_file(claimed, config_path, metrics_store, processed)

                if ok:
                    # Move processed file to processed/ (we already wrote .out there)
                    try:
                        dest = processed / claimed.name
                        if dest.exists():
                            dest = processed / (claimed.name + ".dup")
                        shutil.move(str(claimed), str(dest))
                    except Exception as e:
                        print(f"Failed to move completed file {claimed.name} to processed/: {e}")
                else:
                    # On failure, move back to unprocessed for retry
                    try:
                        retry_dest = unprocessed / claimed.name
                        if retry_dest.exists():
                            retry_dest = unprocessed / (claimed.name + ".retry")
                        shutil.move(str(claimed), str(retry_dest))
                        print(f"Moved failed file back to unprocessed/ for retry: {claimed.name}")
                    except Exception as e:
                        print(f"Failed to move failed file {claimed.name} back to unprocessed/: {e}")

                # Small pause between files to avoid tight loop
                time.sleep(0.01)

        except Exception as e:
            metrics_store.record_error("monitor", e)
            print(f"Monitor loop error: {e}")
            time.sleep(1.0)

    print("Monitor stopping")


def start_monitor_in_thread(watch_dir: str, config_path: str, metrics_store: MetricsStore) -> tuple[threading.Thread, threading.Event]:
    stop_event = threading.Event()
    thread = threading.Thread(target=monitor_folder, args=(watch_dir, config_path, metrics_store, 1.0, stop_event), daemon=True)
    thread.start()
    return thread, stop_event


def start_dashboard_server(port: int = 8000) -> threading.Thread:
    """Start FastAPI dashboard server in a background thread.

    This function is retained for backwards compatibility but newer code will prefer
    to use the DashboardServer from dashboard.py when available.
    """
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
        file_stats = metrics_store.get_file_stats()
        return {
            "timestamp": time.time(),
            "processors": stats,
            "file_queue": file_stats,
            "summary": {
                "total_processors": len(stats),
                "total_lines_processed": sum(p.get("count", 0) for p in stats.values()),
                "total_errors": sum(p.get("errors", 0) for p in stats.values())
            }
        }

    @app.get("/trace")
    async def get_trace(limit: int = 100):
        """Get recent line traces."""
        traces = metrics_store.get_traces(limit=limit)
        return {
            "timestamp": time.time(),
            "traces": traces,
            "total_traces": len(traces),
            "trace_enabled": metrics_store.trace_enabled
        }

    @app.get("/errors")
    async def get_errors(limit: int = 50):
        """Get recent errors."""
        errors = metrics_store.get_errors(limit=limit)
        return {
            "timestamp": time.time(),
            "errors": errors,
            "total_errors": len(errors)
        }

    def run_server():
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="error", access_log=False)

    # Start server in daemon thread
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(0.5)
    return thread


# --- Public run API (backwards compatible) ---

def run(
    input_path: str,
    config_path: str,
    output_path: Optional[str],
    trace_enabled: bool = False,
    dashboard_enabled: bool = True,
    dashboard_port: int = 8000,
    max_traces: int = 1000,
    max_errors: int = 100,
    watch_dir: Optional[str] = None,
) -> None:
    """Run the tag-based routing engine.

    If watch_dir is provided the system will run in folder-monitor mode. Otherwise
    it behaves like the legacy single-file runner (processing input_path once).
    """
    metrics_store = MetricsStore.get_instance(max_traces=max_traces, max_errors=max_errors)
    metrics_store.set_trace_enabled(trace_enabled)

    dashboard_thread = None
    if dashboard_enabled:
        # Prefer DashboardServer from dashboard.py if available (keeps richer UI)
        try:
            from dashboard import DashboardServer
            dashboard_server = DashboardServer(metrics_store)
            dashboard_thread = dashboard_server.start(port=dashboard_port)
            print(f"Dashboard started at http://localhost:{dashboard_port}")
        except Exception:
            print("Falling back to simple dashboard server")
            dashboard_thread = start_dashboard_server(port=dashboard_port)

    # If watch_dir provided -> start monitor and block
    if watch_dir:
        monitor_thread, stop_event = start_monitor_in_thread(watch_dir, config_path, metrics_store)
        print("File monitor started. Press Ctrl+C to exit.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutdown requested, stopping monitor...")
            stop_event.set()
            monitor_thread.join(timeout=2.0)
            print("Stopped.")
        return

    # Legacy single-file behavior (process once)
    try:
        print(f"Reading lines from: {input_path}")
        lines = read_lines(input_path)

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

        output_lines = run_router(start_tag, lines, nodes)

        if output_path:
            print(f"Writing output to: {output_path}")
        else:
            print("Writing output to console")

        write_output(output_lines, output_path)

    except Exception as e:
        metrics_store.record_error("pipeline", e, None)
        print(f"Pipeline error: {e}")
        raise


# Legacy function signature for backwards compatibility
def run_legacy(input_path: str, config_path: str, output_path: Optional[str]) -> None:
    run(input_path, config_path, output_path)


if __name__ == "__main__":
    WATCH_DIR = "watch_dir"
    CONFIG_PATH = "pipeline.yaml"

    run(
        input_path=None,         # not needed in daemon mode
        config_path=CONFIG_PATH,
        output_path=None,        # not needed in daemon mode
        trace_enabled=True,
        dashboard_enabled=True,
        dashboard_port=8000,
        max_traces=1000,
        max_errors=100,
        watch_dir=WATCH_DIR,     # 👈 enables daemon mode
    )
