import sys
import typer
from typing_extensions import Annotated




def main(name: Annotated[str, typer.Argument()] = "Sreyas" , formal: bool = False):
    '''Test docstring bois'''
    if formal:
        print(f"Formal Hello {name}")
    else:
        print("Just Hello, NO Formal")
    # for line in sys.stdin:
    #     print(line.strip().upper())


if __name__ == "__main__":
    typer.run(main)