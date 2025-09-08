from typing import Iterator, Tuple, List

class JoinEveryTwoLines:
    def __init__(self, n: int = 2, sep: str = " ", tag: str = "joined"):
        self.n = n
        self.sep = sep
        self.tag = tag

    def __call__(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        buffer = []
        for line in lines:
            buffer.append(line)
            if len(buffer) == self.n:
                yield [self.tag], self.sep.join(buffer)
                buffer = []
        if buffer:
            yield [self.tag], self.sep.join(buffer)
