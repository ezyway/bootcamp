from typing import Iterator, Tuple, List
from processors.base import BaseProcessor

class Tagger(BaseProcessor):
    def process(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        for line in lines:
            if "ERROR" in line:
                yield ["error"], line
            elif "WARN" in line:
                yield ["warn"], line
            else:
                yield ["trimmed"], line
