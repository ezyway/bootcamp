import sys
from rich.console import Console

def main() -> None:
    console = Console()
    
    who = sys.argv[1] if len(sys.argv) > 1 else "world"
    
    console.print(f"Hello, [bold red]{who}[/bold red]")
    # OR
    console.print(f"Hello, {who}", style='underline blue')
