from typing import Iterator, Tuple, List
from typez import ProcessorFn

class TagError:
    """
    Tags lines containing the word 'ERROR' with ['error'].
    Otherwise tags with ['general'].
    """
    def __call__(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        for line in lines:
            if "ERROR" in line:
                yield (["error"], line)
            else:
                yield (["general"], line)


class TagWarn:
    """
    Tags lines containing the word 'WARN' with ['warn'].
    Otherwise tags with ['general'].
    """
    def __call__(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        for line in lines:
            if "WARN" in line:
                yield (["warn"], line)
            else:
                yield (["general"], line)
