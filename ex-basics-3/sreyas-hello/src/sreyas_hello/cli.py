import typer
from .hello import say_hello

# Force app as a group by preventing direct execution
app = typer.Typer(
    help="Say hello in different ways.",
    no_args_is_help=True  # This forces subcommand structure
)

@app.command("hello")
def hello(name: str = "World"):
    """Say hello to someone (or World)."""
    msg = say_hello(name)
    print(f"Hello {msg}")

def cli():
    app()

if __name__ == "__main__":
    cli()
