from typing import Any, Literal, Optional, Union, List, Dict
from io import BytesIO
import os
import requests
from PIL import Image
import numpy as np
import tempfile
import base64
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
import glob
from tqdm import tqdm
import json

# TODO:
# support other input types such as lists, tensors, ...


def load_img(
    img: Union[str, bytes, np.ndarray, Image.Image],
    output_type: Literal["pil", "numpy", "str", "base64", "ascii", "ansi", "url"] = "pil",
    input_type: Literal["auto", "base64", "file", "url", "numpy", "pil"] = "auto",
) -> Any:
    """Loads an image from various sources and returns it in a specified format.

    Args:
        img: The input image. Can be a base64 string, a file path, a URL,
            a NumPy array, or a Pillow Image object.
        output_type: The desired output type. Can be "pil" (Pillow Image),
            "numpy" (NumPy array), "str" (file path), "base64" (base64 string),
            "ascii" (ASCII art), "ansi" (ANSI art), or "url" (a public URL
            after uploading to a temporary hosting service).
        input_type: The type of the input image. If set to "auto", the function
            will try to automatically determine the type.

    Returns:
        The loaded image in the specified output type.

    Examples:
        ```python
        # Convert to ASCII art
        ascii_art = load_img("image.jpg", output_type="ascii")

        # Convert to ANSI art
        ansi_art = load_img("image.png", output_type="ansi")

        # Upload an image and get a temporary URL
        # Note: This requires an active internet connection.
        # url = load_img("image.png", output_type="url")
        # print(f"Image available at: {url}")
        ```
    """
    try:
        img, original_name = load(img, input_type)
        
        # Validate loaded image
        is_valid, error_msg = validate_image(img.copy())
        if not is_valid:
            raise ValueError(f"Invalid image: {error_msg}")
        
        if output_type == "pil":
            return img
        elif output_type == "numpy":
            return np.array(img)
        elif output_type == "str":
            secure_temp_dir = tempfile.mkdtemp(prefix="loadimg_", suffix="_folder")
            file_name = original_name or f"{uuid.uuid4()}.png"
            path = os.path.join(secure_temp_dir, file_name)
            img.save(path)
            return path
        elif output_type == "base64":
            img_type = img.format or "PNG"
            with BytesIO() as buffer:
                img.save(buffer, format=img_type)
                img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return f"data:image/{img_type.lower()};base64,{img_str}"
        elif output_type == "url":
            upload_url = "https://uguu.se/upload"
            with BytesIO() as buffer:
                img_format = img.format or "PNG"
                img.save(buffer, format=img_format)
                buffer.seek(0)
                
                file_name = original_name or f"{uuid.uuid4()}.{img_format.lower()}"

                files = {'files[]': (file_name, buffer.getvalue(), f'image/{img_format.lower()}')}
                
                try:
                    # Added a timeout for robustness
                    response = requests.post(upload_url, files=files, timeout=15)
                    response.raise_for_status()
                    # The response body from uguu.se is expected to be the direct URL
                    reply =  response.text.strip()
                    return json.loads(reply)["files"][0]["url"]
                except requests.exceptions.RequestException as e:
                    raise IOError(f"Failed to upload image to {upload_url}: {e}") from e
        elif output_type == "ascii":
            return image_to_ascii(img)
        elif output_type == "ansi":
            return image_to_ansi(img)
        else:
            raise ValueError(f"Unsupported output type: {output_type}")
            
    except Exception as e:
        raise ValueError(f"Failed to load image: {str(e)}") from e


def load_imgs(
    imgs: Union[str, List[Union[str, bytes, np.ndarray, Image.Image]]],
    output_type: Literal["pil", "numpy", "str", "base64", "ascii", "ansi", "url"] = "pil",
    input_type: Literal["auto", "base64", "file", "url", "numpy", "pil"] = "auto",
    max_workers: int = 1,
    glob_pattern: str = "*",
) -> Dict[str, Any]:
    """Loads multiple images from various sources.

    Args:
        imgs: Can be:
            - Directory path (str)
            - List of image sources
            - Glob pattern
        output_type: The desired output type. Can be "pil", "numpy", "str", "base64", "ascii", "ansi", or "url".
        input_type: The type of input images
        max_workers: Max number of parallel workers
        glob_pattern: Pattern for filtering files when imgs is a directory

    Returns:
        Dict[str, Any]: Dictionary mapping filenames to loaded images
    """
    image_paths = []
    
    # Handle different input types
    if isinstance(imgs, str):
        if os.path.isdir(imgs):
            # Load from directory
            pattern = os.path.join(imgs, glob_pattern)
            image_paths = glob.glob(pattern)
        else:
            # Single file or URL
            image_paths = [imgs]
    else:
        # List of sources
        image_paths = imgs if isinstance(imgs, list) else [imgs]

    results = {}
    
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create tasks
        future_to_path = {
            executor.submit(load_img, path, output_type, input_type): path
            for path in image_paths
        }
        
        # Process with progress bar
        for future in tqdm(future_to_path, desc="Loading images"):
            path = future_to_path[future]
            try:
                result = future.result()
                key = os.path.basename(path) if isinstance(path, str) else str(uuid.uuid4())
                results[key] = result
            except Exception as e:
                print(f"Failed to load {path}: {e}")

    return results


def starts_with(pattern: str, url: str):
    """
    Check if a URL starts with a given pattern, considering multiple prefixes.

    Args:
        pattern (str): The pattern to match at the start of the URL
        url (str): The full URL to check

    Returns:
        bool: True if the URL starts with the pattern, False otherwise
    """
    return url.startswith(pattern) or url.startswith(f"https://{pattern}")


def download_image(url: str):
    """Downloads an image from a URL and returns it as a Pillow Image."""
    try:
        # GitHub raw file
        if starts_with("github", url) and "raw=true" not in url:
            url += "?raw=true"

        # Google Drive URL
        elif starts_with("drive", url) and ("uc?id=" not in url):
            if "/view" in url or url.endswith("/"):
                url = "/".join(url.split("/")[:-1])
            url = "https://drive.google.com/uc?id=" + url.split("/")[-1]

        # Hugging Face URL
        elif starts_with("hf.co", url) or starts_with("huggingface.co", url):
            url = url.replace("/blob/", "/resolve/")

        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))

    except requests.exceptions.RequestException as e:
        print(f"Error downloading image from {url}: {e}")
        return None


def load(img, input_type="auto") -> tuple[Image.Image, Optional[str]]:
    """Loads an image from various sources and returns it as a Pillow Image along with the original file name if available."""
    original_name = None

    if input_type == "auto":
        if isBase64(img):
            input_type = "base64"
        elif isinstance(img, str):
            if os.path.isfile(img):
                input_type = "file"
            else:
                input_type = "url"
        elif isinstance(img, np.ndarray):
            input_type = "numpy"
        elif isinstance(img, Image.Image):
            input_type = "pil"
        else:
            raise ValueError(
                f"Invalid input type: {input_type}. Expected one of: 'base64', 'file', 'url', 'numpy', 'pil'"
            )

    if input_type == "base64":
        if isinstance(img, str):
            img = re.sub(r"^data:image\/[a-zA-Z]+;base64,", "", img)
            image_bytes = base64.b64decode(img)
            image_file = BytesIO(image_bytes)
            return Image.open(image_file), None
        else:
            image_bytes = base64.b64decode(img)
            image_file = BytesIO(image_bytes)
            return Image.open(image_file), None
    elif input_type == "file":
        original_name = os.path.basename(img)
        return Image.open(img), original_name
    elif input_type == "url":
        out = download_image(img)
        if out is None:
            raise ValueError(f"could not download {img}")
        else:
            original_name = os.path.basename(img.split("?")[0])
            return out, original_name
    elif input_type == "numpy":
        return Image.fromarray(img), None
    elif input_type == "pil":
        return img, None
    else:
        raise ValueError(
            f"Invalid input type: {input_type}. Expected one of: 'base64', 'file', 'url', 'numpy', 'pil'"
        )


def isBase64(sb):
    """
    checks if the input object is base64
    """
    try:
        if isinstance(sb, str):
            sb = re.sub(r"^data:image\/[a-zA-Z]+;base64,", "", sb)
            sb_bytes = bytes(sb, "ascii")
        elif isinstance(sb, bytes):
            sb_bytes = sb
        return base64.b64encode(base64.b64decode(sb_bytes)) == sb_bytes
    except Exception:
        return False


def image_to_ascii(
    image: Image.Image, new_width: int = 100, ascii_chars: str = "@%#*+=-:. "
) -> str:
    """Convert a Pillow image to ASCII art."""
    grayscale_image = image.convert("L")
    width, height = grayscale_image.size
    aspect_ratio = height / width
    new_height = int(aspect_ratio * new_width)
    resized_image = grayscale_image.resize((new_width, new_height))

    pixels = resized_image.getdata()
    ascii_str = ""
    for i, pixel_value in enumerate(pixels):
        index = (pixel_value * (len(ascii_chars) - 1)) // 255
        ascii_str += ascii_chars[index]
        if (i + 1) % new_width == 0:
            ascii_str += "\n"
    return ascii_str


def image_to_ansi(image: Image.Image, new_width: int = 100) -> str:
    """Convert a Pillow image to ANSI art using 24-bit color codes."""
    width, height = image.size
    aspect_ratio = height / width
    new_height = int(aspect_ratio * new_width)
    resized_image = image.resize((new_width, new_height))
    rgb_image = resized_image.convert("RGB")

    ansi_lines = []
    for y in range(new_height):
        line = []
        for x in range(new_width):
            r, g, b = rgb_image.getpixel((x, y))
            ansi_code = f"\x1b[48;2;{r};{g};{b}m "
            line.append(ansi_code)
        ansi_lines.append("".join(line) + "\x1b[0m")
    return "\n".join(ansi_lines)


def validate_image(img: Image.Image) -> tuple[bool, str]:
    """Validates an image for basic requirements.
    
    Args:
        img: PIL Image to validate
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    if not isinstance(img, Image.Image):
        return False, "Input is not a PIL Image"
    
    if img.size[0] * img.size[1] == 0:
        return False, "Image has zero dimensions"
        
    try:
        img.verify()
        return True, ""
    except Exception as e:
        return False, f"Image verification failed: {str(e)}"
