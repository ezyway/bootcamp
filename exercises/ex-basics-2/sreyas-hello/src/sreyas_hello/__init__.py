import sys
from rich.console import Console

def main() -> None:
    console = Console()
    
    who = sys.argv[1] if len(sys.argv) > 1 else "world"
    
    console.print(f"Hello, [bold red]{who}[/bold red]")
    console.print(f"Hello, {who}", style='underline blue')
    console.print("Hello [blue]Alice[/blue]") 
    console.print("Hello [bold green]Alice[/]")      # Bold green ([/] closes all tags)
    console.print("Hello [white on red]Alice[/]")    # White on red background
    console.print("Hello [bold italic cyan]Alice[/]")

