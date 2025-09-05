import typer
from typing_extensions import Annotated
from dotenv import load_dotenv

from main import run

load_dotenv()
app = typer.Typer(help="Run a DAG-based line processing pipeline.")

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
):
    """
    Run a DAG pipeline on input lines. Each processor can yield tagged lines, which
    are routed according to the DAG config.
    """
    run(input, config, output)

if __name__ == "__main__":
    app()
