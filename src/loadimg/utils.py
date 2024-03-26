from typing import Any, Literal, Union
import requests
from PIL import Image
from io import BytesIO
from os import path
import numpy as np
# TODO:
# support output_type parameter to change the output type
# support other input types such as lists, Bytes, tensors, torch tensors, ...


def download_image(url: str):
    """A function to get a Pillow image from a URL."""
    try:
        response = requests.get(url, timeout=5)  # Timeout set to 5 seconds
        response.raise_for_status()  # Raise an exception for HTTP errors
        return Image.open(BytesIO(response.content))
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image from {url}: {e}")
        return None  # Return None if there's an error


SUPPORTED_TYPES = Union[str, np.ndarray, Image.Image]


def load_img(
    img: SUPPORTED_TYPES,
    # output_type=Literal["PIL"]
) -> Any:
    """takes an input image of type any and returns"""
    # file path or url
    if isinstance(img, str):
        if path.isfile(img):
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
        raise ValueError(
            f"""expected one of the following types :{SUPPORTED_TYPES.__args__}, 
            but got {type(img)}, please head to https://github.com/not-lain/loadimg/issues and past your input type so we will support it soon
            """
        )
