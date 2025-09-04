from .base import streamify

def to_uppercase(line: str) -> str:
    return line.upper()

# Stream-compatible processor
upper_processor = streamify(to_uppercase)
