from typing import Iterator, Tuple, List

class BaseProcessor:
    """
    Base class for all processors.
    Provides a consistent interface and optional internal state.
    """
    def __init__(self):
        self.state = {}

    def process(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        """
        Override this in subclasses.
        Yield (tags, line) tuples for next routing step.
        """
        raise NotImplementedError

    def __call__(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        return self.process(lines)

# Example: LineCounter using standardized BaseProcessor
class LineCounter(BaseProcessor):
    def __init__(self, tag: str = "default"):
        super().__init__()
        self.state["count"] = 0
        self.tag = tag

    def process(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        for line in lines:
            self.state["count"] += 1
            yield [self.tag], f"{self.state['count']}: {line}"

# Example: Streamify helper for stateless functions
def streamify(fn, tag: str = "default"):
    """
    Wraps a stateless function into a BaseProcessor-compatible callable.
    """
    class StatelessProcessor(BaseProcessor):
        def process(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
            for line in lines:
                yield [tag], fn(line)
    return StatelessProcessor()
