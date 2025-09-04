import os
from typing import Iterator, Optional
from pipeline import get_pipeline
from core import process_lines


def read_lines(path: str) -> Iterator[str]:
    with open(path, "r") as file:
        for line in file:
            yield line.rstrip("\n")


def write_output(lines: Iterator[str], output_file: Optional[str]) -> None:
    if output_file is None:
        for line in lines:
            print(line)
    else:
        output_file = os.path.abspath(os.path.expanduser(output_file))
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, "w") as file:
            for line in lines:
                file.write(line + "\n")


def run(input_path: str, mode: str, output_path: Optional[str]) -> None:
    lines = read_lines(input_path)
    processors = get_pipeline(mode)
    transformed = process_lines(lines, processors)
    write_output(transformed, output_path)