import os
import sys


def main():
    print("This is arguments")
    print(f"{sys.argv}")
    print("This is environment", flush=True)
    for key, value in os.environ.items():
        print(f"{key} : {value}", flush=True)


if __name__ == "__main__":
    main()
