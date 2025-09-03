import sys


def main():
    for line in sys.stdin:
        print(line.strip().upper())


if __name__ == "__main__":
    main()