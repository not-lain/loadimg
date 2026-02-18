import typer
import shutil
from .utils import load_img, resize_image


def loadimg_cli(
    img: str = typer.Argument(..., help="Input image (file path, URL, or base64 string)"),
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
    fit: bool = typer.Option(
        True, "--fit", "-f", help="Fit the image to the terminal width"
    ),
):
    """
    Load and convert images from various sources.
    """
    if fit:
        max_width = shutil.get_terminal_size().columns
        result = load_img(img=img, output_type="pil", input_type=input_type)
        result = resize_image(result, max_width)
        result = load_img(result, output_type=output_type)
    else : 
        result = load_img(img,output_type=output_type,input_type=input_type)
    if isinstance(result, str):
        print(result)
    else:
        print(f"Image converted successfully to {output_type} format")


def main():
    typer.run(loadimg_cli)


if __name__ == "__main__":
    main()
