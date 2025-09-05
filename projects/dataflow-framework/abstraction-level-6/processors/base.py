from typing import Iterator, Callable, Tuple, List

ProcessorFn = Callable[[Iterator[str]], Iterator[Tuple[List[str], str]]]

def streamify(fn: Callable[[str], str], tag: str = "default") -> ProcessorFn:
    def wrapper(lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        for line in lines:
            yield [tag], fn(line)
    return wrapper

class LineCounter:
    def __init__(self, tag: str = "default"):
        self.count = 0
        self.tag = tag

    def __call__(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        for line in lines:
            self.count += 1
            yield [self.tag], f"{self.count}: {line}"
