import argparse
import sys

try:
    from .utils import load_img
except ImportError:
    from utils import load_img


def main():
    parser = argparse.ArgumentParser(
        prog="loadimg", description="Load and convert images from various sources"
    )
    parser.add_argument("input", help="Input image (file path, URL, or base64 string)")
    parser.add_argument(
        "--output-type",
        choices=["pil", "numpy", "str", "base64", "ascii", "ansi", "url"],
        default="ansi",
        help="Output format (default: ansi)",
    )
    parser.add_argument(
        "--input-type",
        choices=["auto", "base64", "file", "url", "numpy", "pil"],
        default="auto",
        help="Input type (default: auto)",
    )

    args = parser.parse_args()
    if not hasattr(args, "input"):
        parser.print_help()
        exit(1)

    try:
        result = load_img(
            args.input, output_type=args.output_type, input_type=args.input_type
        )
        if isinstance(result, str):
            print(result)
        else:
            print(f"Image converted successfully to {args.output_type} format")
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
