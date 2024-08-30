from typing import Any, Literal, Union
from io import BytesIO
import os
import requests
from PIL import Image
import numpy as np
import tempfile
import base64
import inspect

# TODO:
# support other input types such as lists, tensors, ...


def load_img(
    img: Union[str, bytes, np.ndarray, Image.Image],
    output_type: Literal["pil", "numpy", "str", "base64"] = "pil",
) -> Any:
    """
    takes an input image of type any and returns an image in any one of the supported output types
    Args :

    how to use :

    ```python
    from loadimg import load_img
    load_img(img,output_type="pil")
    ```
    """
    img = load(img)
    if output_type == "pil":
        return img
    elif output_type == "numpy":
        return np.array(img)
    elif output_type == "str":
        secure_temp_dir = tempfile.mkdtemp(prefix="loadimg_", suffix="_folder")
        path = os.path.join(secure_temp_dir, "temp_image.png")
        img.save(path)
        return path
    elif output_type == "base64":
        img_file = BytesIO()
        img.save(img_file, format="PNG")
        img_bytes = img_file.getvalue()
        img_b64 = base64.b64encode(img_bytes)
        return img_b64


def download_image(url: str):
    """A function to get a Pillow image from a URL."""
    try:
        if "github" in url and "raw=true" not in url:
            url += "?raw=true"
        elif "drive" in url and "uc?id=" not in url:
            if "/view" in url or url.endswith("/"):
                url = "/".join(url.split("/")[:-1])
            url = "https://drive.google.com/uc?id=" + url.split("/")[-1]
        elif "hf.co" or "huggingface.co" in url:
            url = url.replace("/blob/", "/resolve")
        response = requests.get(url, timeout=5)  # Timeout set to 5 seconds
        response.raise_for_status()  # Raise an exception for HTTP errors
        return Image.open(BytesIO(response.content))
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image from {url}: {e}")
        return None  # Return None if there's an error


def load(img) -> Image.Image:
    """loads the img and returns a pillow image"""
    # base64 (str or bytes)
    if isBase64(img):
        image_bytes = base64.b64decode(img)
        image_file = BytesIO(image_bytes)
        return Image.open(image_file)
    # file path or url
    elif isinstance(img, str):
        if os.path.isfile(img):
            return Image.open(img)
        else:
            out = download_image(img)
            if out is None:
                raise ValueError(f"could not download {img}")
            else:
                return out
    # numpy array
    elif isinstance(img, np.ndarray):
        return Image.fromarray(img)
    # pillow image
    elif isinstance(img, Image.Image):
        return img
    else:
        available_types = [
            i.__name__
            for i in inspect.signature(load_img).parameters["img"].annotation.__args__
        ]
        available_types = ", ".join(available_types)
        raise ValueError(
            f"expected one of the following types :{available_types}, but got {type(img).__name__}"
        )


def isBase64(sb):
    """
    checks if the input object is base64
    """
    try:
        if isinstance(sb, str):
            # If there's any unicode here, an exception will be thrown and the function will return false
            sb_bytes = bytes(sb, "ascii")
        elif isinstance(sb, bytes):
            sb_bytes = sb
        return base64.b64encode(base64.b64decode(sb_bytes)) == sb_bytes
    except Exception:
        return False
