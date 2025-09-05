from typing import Iterator, Tuple, List
from typez import ProcessorFn

class terminal:
    """Terminal processor that emits 'end' for all lines."""
    def __call__(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        for line in lines:
            yield (["end"], line)