from .base import streamify

def to_snakecase(line: str) -> str:
    return line.replace(" ", "_").lower()

# Stream-compatible processor
snake_processor = streamify(to_snakecase)
