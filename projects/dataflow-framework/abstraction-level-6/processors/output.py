from typing import Iterator, Tuple, List
from processors.base import BaseProcessor

class Terminal(BaseProcessor):
    def process(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        for line in lines:
            yield ["end"], line
