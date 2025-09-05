from typing import Iterator, Tuple, List, Callable

# Each processor takes an iterator of lines and yields (tags, line) pairs
ProcessorFn = Callable[[Iterator[str]], Iterator[Tuple[List[str], str]]]
