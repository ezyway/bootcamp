import typer
from typing_extensions import Annotated
from dotenv import load_dotenv
from main import run
import os

load_dotenv()

app = typer.Typer(help="Run a DAG-based line processing pipeline with observability.")

@app.command()
def main(
    input: Annotated[str, typer.Argument()],
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
        typer.Option("--dashboard/--no-dashboard", help="Start web dashboard for live metrics (runs on http://localhost:8000)."),
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
    Run a DAG pipeline on input lines. Each processor can yield tagged lines, which
    are routed according to the DAG config.
    
    The system includes built-in observability features:
    - Real-time metrics per processor (count, timing, errors)
    - Optional line tracing through the DAG
    - Web dashboard with live stats, traces, and error logs
    """
    
    # Set environment variable for tracing (can be used by other components)
    if trace:
        os.environ['TRACE_ENABLED'] = 'true'
    else:
        os.environ['TRACE_ENABLED'] = 'false'
    
    # Display startup information
    if dashboard:
        typer.echo(f"Starting pipeline with dashboard on http://localhost:{dashboard_port}")
        if trace:
            typer.echo(f"Tracing enabled - storing up to {max_traces} traces")
        else:
            typer.echo("Tracing disabled (use --trace to enable)")
    else:
        typer.echo("Starting pipeline without dashboard")
    
    typer.echo(f"Storing up to {max_errors} errors in memory")
    typer.echo("=" * 60)
    
    # Run the main pipeline
    run(
        input_path=input, 
        config_path=config, 
        output_path=output, 
        trace_enabled=trace,
        dashboard_enabled=dashboard,
        dashboard_port=dashboard_port,
        max_traces=max_traces,
        max_errors=max_errors
    )

if __name__ == "__main__":
    app()
