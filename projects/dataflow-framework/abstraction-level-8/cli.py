import typer
from typing_extensions import Annotated
from dotenv import load_dotenv
from main import run
import os
from pathlib import Path

load_dotenv()

app = typer.Typer(help="Run a DAG-based line processing pipeline with observability.")

@app.command()
def single(
    input: Annotated[str, typer.Argument(help="Input file to process")],
    config: Annotated[
        str,
        typer.Option(help="Path to DAG pipeline config file (YAML). Defaults to pipeline.yaml."),
    ] = "pipeline.yaml",
    output: Annotated[
        str | None,
        typer.Option(help="Specify output file. If not specified, prints to console."),
    ] = None,
    trace: Annotated[
        bool,
        typer.Option("--trace/--no-trace", help="Enable tracing of line journeys through the DAG."),
    ] = False,
    dashboard: Annotated[
        bool,
        typer.Option("--dashboard/--no-dashboard", help="Start web dashboard for live metrics."),
    ] = False,
    dashboard_port: Annotated[
        int,
        typer.Option(help="Port for the web dashboard."),
    ] = 8000,
):
    """
    Process a single file through the DAG pipeline and exit.
    
    Example: python -m cli single input.txt --output result.txt --trace
    """
    if not Path(input).exists():
        typer.echo(f"Error: Input file '{input}' does not exist.", err=True)
        raise typer.Exit(1)
    
    typer.echo(f"Processing single file: {input}")
    if dashboard:
        typer.echo(f"Dashboard available at http://localhost:{dashboard_port}")
    
    run(
        input_path=input,
        config_path=config,
        output_path=output,
        trace_enabled=trace,
        dashboard_enabled=dashboard,
        dashboard_port=dashboard_port,
        watch_dir=None  # Single file mode
    )

@app.command()
def watch(
    watch_dir: Annotated[
        str,
        typer.Option(help="Directory to monitor for new files. Must contain unprocessed/ subfolder."),
    ] = "watch_dir",
    config: Annotated[
        str,
        typer.Option(help="Path to DAG pipeline config file (YAML)."),
    ] = "pipeline.yaml",
    trace: Annotated[
        bool,
        typer.Option("--trace/--no-trace", help="Enable tracing of line journeys through the DAG."),
    ] = True,
    dashboard: Annotated[
        bool,
        typer.Option("--dashboard/--no-dashboard", help="Start web dashboard for live metrics."),
    ] = True,
    dashboard_port: Annotated[
        int,
        typer.Option(help="Port for the web dashboard."),
    ] = 8000,
    max_traces: Annotated[
        int,
        typer.Option(help="Maximum number of traces to keep in memory."),
    ] = 1000,
    max_errors: Annotated[
        int,
        typer.Option(help="Maximum number of errors to keep in memory."),
    ] = 100,
):
    """
    Continuously monitor a directory for new files and process them.
    
    Files should be placed in {watch_dir}/unprocessed/ folder.
    Processed files will be moved to {watch_dir}/processed/ folder.
    
    Example: python -m cli watch --watch-dir ./my_watch_dir
    """
    watch_path = Path(watch_dir)
    unprocessed_dir = watch_path / "unprocessed"
    
    # Create directories if they don't exist
    unprocessed_dir.mkdir(parents=True, exist_ok=True)
    (watch_path / "underprocess").mkdir(exist_ok=True)
    (watch_path / "processed").mkdir(exist_ok=True)
    
    typer.echo(f"Starting file monitoring on: {unprocessed_dir}")
    typer.echo(f"Dashboard available at http://localhost:{dashboard_port}")
    typer.echo("Drop files into the unprocessed/ folder to process them.")
    typer.echo("Press Ctrl+C to stop.")
    typer.echo("=" * 60)
    
    run(
        input_path="",  # Not used in watch mode
        config_path=config,
        output_path=None,  # Not used in watch mode
        trace_enabled=trace,
        dashboard_enabled=dashboard,
        dashboard_port=dashboard_port,
        max_traces=max_traces,
        max_errors=max_errors,
        watch_dir=watch_dir
    )

# Legacy command for backwards compatibility
@app.command(hidden=True)
def main(
    input: Annotated[str, typer.Argument()] = "",
    config: Annotated[str, typer.Option()] = "pipeline.yaml",
    output: Annotated[str | None, typer.Option()] = None,
    trace: Annotated[bool, typer.Option("--trace/--no-trace")] = False,
    dashboard: Annotated[bool, typer.Option("--dashboard/--no-dashboard")] = True,
    dashboard_port: Annotated[int, typer.Option()] = 8000,
    max_traces: Annotated[int, typer.Option()] = 1000,
    max_errors: Annotated[int, typer.Option()] = 100,
):
    """Legacy main command - use 'single' or 'watch' instead."""
    if input:
        # Single file mode
        run(input, config, output, trace, dashboard, dashboard_port, max_traces, max_errors)
    else:
        # Watch mode
        run("", config, output, trace, dashboard, dashboard_port, max_traces, max_errors, "watch_dir")

if __name__ == "__main__":
    app()
