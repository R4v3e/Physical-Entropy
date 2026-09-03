import argparse
import time

from capture import create_sample


def main():
    parser = argparse.ArgumentParser(
        description="Automatically collect Lava RNG samples."
    )

    parser.add_argument(
        "--samples",
        type=int,
        help="Number of samples to capture.",
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=10,
        help="Seconds between captures.",
    )

    args = parser.parse_args()

    if args.samples is None or args.samples <= 0:
        parser.error("--samples must be greater than 0")

    print(f"Starting collection of {args.samples} samples.")
    print(f"Interval: {args.interval} seconds")
    print("Press Ctrl+C to stop.\n")

    for i in range(args.samples):
        print(f"=== Sample {i + 1}/{args.samples} ===")

        try:
            create_sample()
        except Exception as error:
            print(f"Capture failed: {error}")

        if i < args.samples - 1:
            time.sleep(args.interval)

    print("\nCollection finished.")


if __name__ == "__main__":
    main()
