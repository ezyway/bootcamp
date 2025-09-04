import typer
import os
from typing_extensions import Annotated
from dotenv import load_dotenv
from main import run

load_dotenv()

app = typer.Typer()


@app.command()
def main(
    input: Annotated[str, typer.Argument()],
    config: Annotated[
        str,
        typer.Option(help="Path to pipeline config file (YAML). Defaults to pipeline.yaml."),
    ] = "pipeline.yaml",
    output: Annotated[
        str,
        typer.Option(help="Specify output file. If not specified, prints to console."),
    ] = None,
):
    run(input, config, output)


if __name__ == "__main__":
    app()
