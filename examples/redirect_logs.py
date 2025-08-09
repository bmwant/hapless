#!/usr/bin/env python3
import sys


def main():
    print("This is stdout", flush=True, file=sys.stdout)
    print("This is stderr", flush=True, file=sys.stderr)


if __name__ == "__main__":
    main()
