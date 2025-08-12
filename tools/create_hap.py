from hapless import Hapless


def main():
    hapless = Hapless()
    hap = hapless.create_hap("echo 'Test empty hap'")
    print(f"Created {hap}, current status: {hap.status}")


if __name__ == "__main__":
    main()
