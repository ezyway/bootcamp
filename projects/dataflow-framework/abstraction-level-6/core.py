from typing import Iterable
from typez import ProcessorFn


def to_uppercase(line: str) -> str:
    return line.upper()


def to_snakecase(line: str) -> str:
    return line.replace(" ", "_").lower()


def apply_processors(line: str, processors: list[ProcessorFn]) -> str:
    """Apply all processors in sequence to a single line."""
    for processor in processors:
        line = processor(line)
    return line


def process_lines(lines: Iterable[str], processors: list[ProcessorFn]) -> Iterable[str]:
    """Yield processed lines one by one."""
    for line in lines:
        yield apply_processors(line, processors)
