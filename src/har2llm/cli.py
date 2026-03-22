import argparse

from .har_cleaner import process_har

def main():
    parser = argparse.ArgumentParser(description="Process HAR files.")
    parser.add_argument("input", help="Input HAR file")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    result = process_har(args.input)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Processed and saved to {args.output}")
    else:
        print(result)

if __name__ == "__main__":
    main()
