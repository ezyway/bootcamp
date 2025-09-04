from typing import Iterator, Tuple, List

class SplitLines:
    def __init__(self, delimiter: str = ",", tag: str = "split"):
        self.delimiter = delimiter
        self.tag = tag

    def __call__(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        for line in lines:
            for part in line.split(self.delimiter):
                yield [self.tag], part.strip()
