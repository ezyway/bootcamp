from typing import Iterator, Tuple, List
from typez import ProcessorFn

class Tagger:
    """
    Tags lines containing 'ERROR' with ['error'].
    Other lines are tagged ['general'] for further processing.
    """
    def __call__(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        for line in lines:
            if "ERROR" in line:
                yield (["error"], line)
            elif "WARN" in line:
                yield (["warn"], line)
            else:
                yield (["general"], line)

