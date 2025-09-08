from .base import streamify

def to_uppercase(line: str) -> str:
    return line.upper()

upper_processor = streamify(to_uppercase, tag="uppercase")
