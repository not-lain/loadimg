from typing import Any, Literal, Union
from io import BytesIO
import os
import requests
from PIL import Image
import numpy as np
import tempfile
# TODO:
# support output_type parameter to change the output type
# support other input types such as lists, Bytes, tensors, torch tensors, ...


def download_image(url: str):
    """A function to get a Pillow image from a URL."""
    try:
        if "github" in url and "raw=true" not in url:
            url += "?raw=true"
        elif "drive" in url and "uc?id=" not in url:
            if "/view" in url or url.endswith("/"):
                url = "/".join(url.split("/")[:-1])
            url = "https://drive.google.com/uc?id=" + url.split("/")[-1]
        elif "hf.co" or "huggingface.co" in url : 
            url = url.replace("/blob/","/resolve")
        response = requests.get(url, timeout=5)  # Timeout set to 5 seconds
        response.raise_for_status()  # Raise an exception for HTTP errors
        return Image.open(BytesIO(response.content))
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image from {url}: {e}")
        return None  # Return None if there's an error


SUPPORTED_INPUT_TYPES = Union[str, np.ndarray, Image.Image]
SUPPORTED_OUTPUT_TYPES = Literal["pil", "numpy", "str"]


def load_img(
    img: Union[str, np.ndarray, Image.Image],
    output_type: Literal["pil", "numpy", "str"] = "pil",
) -> Any:
    """
    takes an input image of type any and returns a pillow image
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


def load(img: SUPPORTED_INPUT_TYPES) -> Image.Image:
    "loads the img"
    # file path or url
    if isinstance(img, str):
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
