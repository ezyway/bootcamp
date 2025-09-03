def main() -> None:
    import sys
    who = sys.argv[1] if len(sys.argv) > 1 else "world"
    print(f"hello, {who}")
