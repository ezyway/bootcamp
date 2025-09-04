# processors/fanin.py
from typing import Iterator
from .base import ProcessorFn

class JoinEveryTwoLines:
    """
    Join every N lines into one output line.
    Example: join 2 lines:
        ["a", "b", "c", "d"] -> ["a b", "c d"]
    """
    def __init__(self, n: int = 2, sep: str = " "):
        self.n = n
        self.sep = sep

    def __call__(self, lines: Iterator[str]) -> Iterator[str]:
        buffer = []
        for line in lines:
            buffer.append(line)
            if len(buffer) == self.n:
                yield self.sep.join(buffer)
                buffer = []
        if buffer:
            yield self.sep.join(buffer)
