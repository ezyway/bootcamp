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
    mode: Annotated[
        str,
        typer.Option(help="Modes can be uppercase, lowercase or snakecase"),
    ] = os.getenv("DEFAULT_MODE", "lowercase"),
    output: Annotated[
        str,
        typer.Option(help="Specify output file. If not specified, prints to console."),
    ] = None,
):
    run(input, mode, output)


if __name__ == "__main__":
    app()
