from typing import Iterator, Tuple, List
from typez import ProcessorFn

def to_uppercase(lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
    """
    Convert lines to uppercase and emit them with 'end' tag.
    """
    for line in lines:
        yield (["end"], line.upper())

def to_snakecase(lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
    """
    Convert lines to snake_case and emit them with 'end' tag.
    """
    for line in lines:
        yield (["end"], line.replace(" ", "_").lower())

def trim(lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
    """Trim whitespace and emit lines with 'trimmed' tag."""
    for line in lines:
        yield (["trimmed"], line.strip())
