from typing import Any, Literal, Optional, Union, TypeAlias, Tuple
from functools import lru_cache
from pathlib import Path
import re
from io import BytesIO
import base64
import tempfile
import uuid
import requests
from PIL import Image
import numpy as np

# Type aliases
ImageType: TypeAlias = Union[str, bytes, np.ndarray, Image.Image, Path]
OutputType = Literal["pil", "numpy", "str", "base64"]
InputType = Literal["auto", "base64", "file", "url", "numpy", "pil"]

# Compile regex patterns once
BASE64_PATTERN = re.compile(r"^data:image\/[a-zA-Z]+;base64,")


class ImageLoader:
    """A class to handle image loading from various sources and conversion to different formats."""

    def __init__(self):
        """Initialize the ImageLoader with a requests session and cached methods."""
        self.session = requests.Session()
        # Create separate cached methods for hashable inputs
        self._load_from_url_cached = lru_cache(maxsize=128)(self._load_from_url)
        self._load_from_file_cached = lru_cache(maxsize=128)(self._load_from_file)
        self._load_from_base64_cached = lru_cache(maxsize=128)(self._load_from_base64)

    @staticmethod
    def _is_base64(data: Union[str, bytes]) -> bool:
        """
        Check if input is base64 encoded.

        Args:
            data: String or bytes to check

        Returns:
            bool: True if input is valid base64, False otherwise
        """
        try:
            if isinstance(data, str):
                data = BASE64_PATTERN.sub("", data)
                data_bytes = bytes(data, "ascii")
            else:
                data_bytes = data
            return base64.b64encode(base64.b64decode(data_bytes)) == data_bytes
        except Exception:
            return False

    @staticmethod
    def _determine_input_type(img: ImageType) -> InputType:
        """
        Determine the input type of the image.

        Args:
            img: Input image in any supported format

        Returns:
            InputType: Determined input type

        Raises:
            ValueError: If input type cannot be determined
        """
        if isinstance(img, np.ndarray):
            return "numpy"
        if isinstance(img, Image.Image):
            return "pil"
        if isinstance(img, Path):
            return "file"
        if isinstance(img, (str, bytes)):
            if ImageLoader._is_base64(img):
                return "base64"
            if isinstance(img, str):
                return "file" if Path(img).is_file() else "url"
        raise ValueError(f"Cannot determine input type for {type(img)}")

    def _load_from_url(self, url: str) -> Tuple[Image.Image, Optional[str]]:
        """
        Load image from URL with special handling for common platforms.

        Args:
            url: URL to load image from

        Returns:
            Tuple of (PIL Image, filename)

        Raises:
            ValueError: If image cannot be downloaded or loaded
        """
        # Handle special URLs
        if "github.com" in url and "raw=true" not in url:
            url += "?raw=true"
        elif "drive.google.com" in url and "uc?id=" not in url:
            file_id = url.split("/d/")[-1].split("/")[
                0
            ]  # Correct extraction of file_id
            url = f"https://drive.google.com/uc?id={file_id}"
        elif any(x in url for x in ["hf.co", "huggingface.co"]):
            url = url.replace("/blob/", "/resolve/")

        try:
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            return Image.open(BytesIO(response.content)), Path(url).stem
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to download image from {url}: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load image from {url}: {e}")

    def _load_from_file(self, path: str) -> Tuple[Image.Image, str]:
        """
        Load image from file path.

        Args:
            path: Path to image file

        Returns:
            Tuple of (PIL Image, filename)

        Raises:
            ValueError: If file cannot be loaded
        """
        try:
            path_obj = Path(path)
            with open(
                path_obj, "rb"
            ) as f:  # Use context manager to ensure file is closed
                return Image.open(f), path_obj.name
        except Exception as e:
            raise ValueError(f"Failed to load image from file {path}: {e}")

    def _load_from_base64(self, data: Union[str, bytes]) -> Tuple[Image.Image, None]:
        """
        Load image from base64 data.

        Args:
            data: Base64 encoded image data

        Returns:
            Tuple of (PIL Image, None)

        Raises:
            ValueError: If base64 data cannot be decoded or loaded
        """
        try:
            if isinstance(data, str):
                data = BASE64_PATTERN.sub("", data)
            image_bytes = base64.b64decode(data)
            return Image.open(BytesIO(image_bytes)), None
        except Exception as e:
            raise ValueError(f"Failed to load image from base64 data: {e}")

    def _convert_to_output_type(
        self,
        img: Image.Image,
        output_type: OutputType,
        original_name: Optional[str] = None,
    ) -> Any:
        """
        Convert PIL Image to desired output type.

        Args:
            img: PIL Image to convert
            output_type: Desired output format
            original_name: Original filename if available

        Returns:
            Converted image in requested format

        Raises:
            ValueError: If conversion fails
        """
        try:
            if output_type == "pil":
                return img
            elif output_type == "numpy":
                return np.array(img)
            elif output_type == "base64":
                # buffered = BytesIO()
                # img.save(buffered, format=img.format or "PNG")
                # return base64.b64encode(buffered.getvalue()).decode()
                img_type = img.format or "PNG"
                with BytesIO() as buffer:
                    img.save(buffer, format=img_type)
                    img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
                return f"data:image/{img_type.lower()};base64,{img_str}"
            elif output_type == "str":
                # Save to temporary file with original extension if available
                ext = Path(original_name).suffix if original_name else ".png"
                temp_dir = Path(tempfile.gettempdir())
                temp_path = temp_dir / f"{uuid.uuid4()}{ext}"
                img.save(temp_path)
                return str(temp_path)
            else:
                raise ValueError(f"Invalid output type: {output_type}")
        except Exception as e:
            raise ValueError(f"Failed to convert image to {output_type}: {e}")

    def load(
        self, img: ImageType, input_type: InputType = "auto"
    ) -> Tuple[Image.Image, Optional[str]]:
        """
        Load image from various sources with caching for hashable inputs.

        Args:
            img: Input image in any supported format
            input_type: Type of input image, or "auto" to determine automatically

        Returns:
            Tuple of (PIL Image, filename if available)

        Raises:
            ValueError: If image cannot be loaded
        """
        if input_type == "auto":
            input_type = self._determine_input_type(img)

        if input_type == "base64":
            img = re.sub(r"^data:image\/[a-zA-Z]+;base64,", "", img)
            image_bytes = base64.b64decode(img)
            image_file = BytesIO(image_bytes)
            return Image.open(image_file), None
        elif input_type == "file":
            return self._load_from_file_cached(str(img))
        elif input_type == "url":
            return self._load_from_url_cached(str(img))
        elif input_type == "numpy":
            # Ensure the array is in a supported format (uint8)
            if img.dtype != np.uint8:
                img = img.astype(np.uint8)
            return Image.fromarray(img), None
        elif input_type == "pil":
            return img, None

        raise ValueError(f"Invalid input type: {input_type}")


def load_img(
    img: ImageType, output_type: OutputType = "pil", input_type: InputType = "auto"
) -> Any:
    """
    Load an image from various sources and return it in the specified format.

    Args:
        img: Input image (base64 string, file path, URL, NumPy array, or PIL Image)
        output_type: Desired output type ("pil", "numpy", "str", or "base64")
        input_type: Type of input image ("auto", "base64", "file", "url", "numpy", "pil")

    Returns:
        The loaded image in the specified output type

    Raises:
        ValueError: If input type is invalid or image cannot be loaded
    """
    loader = ImageLoader()
    img_pil, original_name = loader.load(img, input_type)
    return loader._convert_to_output_type(img_pil, output_type, original_name)
