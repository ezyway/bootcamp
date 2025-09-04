import os
from typing import Iterator, Optional
from pipeline import get_pipeline

def read_lines(path: str) -> Iterator[str]:
    """Lazily read lines from a file, stripping newlines."""
    with open(path, "r") as file:
        for line in file:
            yield line.rstrip("\n")

def write_output(lines: Iterator[str], output_file: Optional[str]) -> None:
    """
    Write or print processed lines.
        write_output(iter(["a", "b"]), None)  # prints "a" then "b"
        write_output(iter(["a", "b"]), "out.txt")  # writes to file
    """
    if output_file is None:
        for line in lines:
            print(line)
    else:
        output_file = os.path.abspath(os.path.expanduser(output_file))
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w") as file:
            for line in lines:
                file.write(line + "\n")

def run(input_path: str, config_path: str, output_path: Optional[str]) -> None:
    """
    Run the stream-based pipeline:
    1. Read input as iterator
    2. Pass through each processor
    3. Write output
    """
    lines: Iterator[str] = read_lines(input_path)
    processors = get_pipeline(config_path)

    # Apply processors sequentially (streaming)
    for processor in processors:
        lines = processor(lines)

    write_output(lines, output_path)
