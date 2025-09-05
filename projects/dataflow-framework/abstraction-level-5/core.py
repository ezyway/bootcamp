from typing import Iterator, Tuple, List
from typez import ProcessorFn

def to_uppercase(lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
    for line in lines:
        yield (["uppercase"], line.upper())

def to_snakecase(lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
    for line in lines:
        yield (["snake"], line.replace(" ", "_").lower())

def trim(lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
    for line in lines:
        yield (["trimmed"], line.strip())
