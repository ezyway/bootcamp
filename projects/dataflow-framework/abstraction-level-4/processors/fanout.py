# processors/fanout.py
from typing import Iterator
from .base import ProcessorFn

class SplitLines:
    """
    Split each line by a delimiter and emit multiple lines.
    Example:
        "apple,banana,pear" -> "apple", "banana", "pear"
    """
    def __init__(self, delimiter: str = ","):
        self.delimiter = delimiter

    def __call__(self, lines: Iterator[str]) -> Iterator[str]:
        for line in lines:
            for part in line.split(self.delimiter):
                yield part.strip()
