from typing import Iterator, Tuple, List
from processors.base import BaseProcessor

class ToUppercase(BaseProcessor):
    def process(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        for line in lines:
            yield ["end"], "ERROR: " + line.upper()

class ToSnakecase(BaseProcessor):
    def process(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        for line in lines:
            yield ["end"], "WARN: " + line.replace(" ", "_").lower()

class Trim(BaseProcessor):
    def process(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        for line in lines:
            yield ["end"], "INFO: " + line.strip()
