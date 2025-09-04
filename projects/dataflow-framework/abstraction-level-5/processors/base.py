from typing import Iterator, Callable

ProcessorFn = Callable[[Iterator[str]], Iterator[str]]

def streamify(fn: Callable[[str], str]) -> ProcessorFn:
    """
    Wrap a simple str->str function to work on a stream of lines.
    """
    def wrapper(lines: Iterator[str]) -> Iterator[str]:
        for line in lines:
            yield fn(line)
    return wrapper

class LineCounter:
    """
    Stateful processor that counts lines seen and emits a tuple:
    "<line_number>: <line>"
    """
    def __init__(self):
        self.count = 0

    def __call__(self, lines: Iterator[str]) -> Iterator[str]:
        for line in lines:
            self.count += 1
            yield f"{self.count}: {line}"
