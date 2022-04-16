import sys
import time


def main():
    print("Failing in 1 sec", flush=True)
    time.sleep(1)
    sys.exit(1)


if __name__ == "__main__":
    main()
