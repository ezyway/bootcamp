import sys
import os
import typer
from typing_extensions import Annotated, Iterator, Optional
from dotenv import load_dotenv

load_dotenv()

def read_lines(path: str) -> Iterator[str]:
    '''Read lines from a file and yield them without trailing newlines.'''
    
    with open(path, 'r') as file:
        for line in file:
            yield line.rstrip('\n')


def transform_line(line: str, mode: str) -> str:
    '''Transform a line of text based on the given mode.'''

    if mode == 'uppercase':
        return line.upper()
    elif mode == 'lowercase':
        return line.lower()
    elif mode == 'snakecase':
        return line.replace(' ','_').lower()
    else:
        raise ValueError(f"Invalid Mode {mode}")


def write_output(lines: Iterator[str], output_file: Optional[str]) -> None:
    '''Write lines either to stdout or to a specified file.'''

    if output_file == None:
        for line in lines:
            print(line)
    else:
        output_file = os.path.abspath(os.path.expanduser(output_file))
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(os.path.join(output_file), 'w') as file:
            for line in lines:
                file.write(line + '\n')


def main(
        input: Annotated[str, typer.Argument()],
        mode: Annotated[str, typer.Option(help='Modes can be uppercase, lowercase or snakecase')] = os.getenv('DEFAULT_MODE', 'lowercase'),
        output: Annotated[str, typer.Option(help='Specify the location of the output file. If not specified, then prints in the console.')] = None):
    '''Transform file contents and print or save results.'''

    lines = read_lines(input)
    transformed = (transform_line(line, mode) for line in lines)
    write_output(transformed, output if output else None)


if __name__ == "__main__":
    typer.run(main)