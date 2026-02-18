import typer

from .utils import load_img


def loadimg_cli(
    input: str = typer.Argument(..., help="Input image (file path, URL, or base64 string)"),
    output_type: str = typer.Option(
        "ansi",
        "--output-type",
        help="Output format (pil, numpy, str, base64, ascii, ansi, url)",
    ),
    input_type: str = typer.Option(
        "auto",
        "--input-type",
        help="Input type (auto, base64, file, url, numpy, pil)",
    ),
):
    """
    Load and convert images from various sources.
    """
    try:
        result = load_img(input, output_type=output_type, input_type=input_type)
        if isinstance(result, str):
            print(result)
        else:
            print(f"Image converted successfully to {output_type} format")
    except Exception as e:
        print(f"Error: {e}")
        raise typer.Exit(code=1)


def main():
    typer.run(loadimg_cli)


if __name__ == "__main__":
    main()
