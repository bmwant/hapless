import time


def main():
    # this should be running for about 2 hours
    for i in range(1000):
        print(".", end="", flush=True)
        time.sleep(10)


if __name__ == "__main__":
    main()
