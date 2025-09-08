import os
from typing import Iterator, Optional
from pipeline import build_routing, run_router

def read_lines(path: str) -> Iterator[str]:
    """Read lines from a file, stripping newlines."""
    with open(path, "r") as file:
        for line in file:
            yield line.rstrip("\n")

def write_output(lines: Iterator[str], output_file: Optional[str]) -> None:
    """Write lines to a file or print to console if output_file is None."""
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
    """Run the tag-based routing engine on input lines."""
    lines = read_lines(input_path)
    nodes = build_routing(config_path)

    import yaml
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)
    start_tag = cfg.get("start", "start")

    output_lines = run_router(start_tag, lines, nodes)
    write_output(output_lines, output_path)
