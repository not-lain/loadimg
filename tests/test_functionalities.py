import unittest
from unittest.mock import Mock, patch, ANY
import numpy as np
from PIL import Image
import base64
from pathlib import Path
import tempfile
import shutil
import requests
from io import BytesIO

from loadimg import ImageLoader, load_img


class TestImageLoader(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.loader = ImageLoader()
        # Create a simple test image with known dimensions and color
        self.test_image = Image.new("RGB", (100, 100), color="red")
        self.test_array = np.array(self.test_image)

        # Create a temporary directory for test files
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "test_image.png"
        self.test_image.save(self.test_file)

        # Create base64 test data
        buffer = BytesIO()
        self.test_image.save(buffer, format="PNG")
        self.test_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        self.test_base64_with_header = f"data:image/png;base64,{self.test_base64}"

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_pil_image(self):
        """Test loading a PIL Image."""
        img, name = self.loader.load(self.test_image)
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (100, 100))
        self.assertIsNone(name)

    def test_load_numpy_array(self):
        """Test loading a numpy array."""
        img, name = self.loader.load(self.test_array)
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (100, 100))
        self.assertIsNone(name)

        # Test different numpy array types
        for dtype in [np.uint8, np.int32, np.float32]:
            arr = np.array(self.test_array, dtype=dtype)
            img, name = self.loader.load(arr)
            self.assertIsInstance(img, Image.Image)
            self.assertEqual(img.size, (100, 100))

    def test_load_file(self):
        """Test loading from a file path."""
        # Test with string path
        img, name = self.loader.load(str(self.test_file))
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (100, 100))
        self.assertEqual(name, "test_image.png")

        # Test with Path object
        img, name = self.loader.load(self.test_file)
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(name, "test_image.png")

        # Test file not found
        with self.assertRaises(ValueError):
            self.loader.load(str(self.temp_dir / "nonexistent.png"))

    def test_load_base64(self):
        """Test loading from base64 string."""
        # Test with header
        img1, name1 = self.loader.load(self.test_base64_with_header)
        self.assertIsInstance(img1, Image.Image)
        self.assertEqual(img1.size, (100, 100))
        self.assertIsNone(name1)

        # Test without header
        img2, name2 = self.loader.load(self.test_base64)
        self.assertIsInstance(img2, Image.Image)
        self.assertEqual(img2.size, (100, 100))
        self.assertIsNone(name2)

        # Test invalid base64
        with self.assertRaises(ValueError):
            self.loader.load("invalid_base64_string")

    @patch("requests.Session.get")
    def test_load_url(self, mock_get):
        """Test loading from URL."""
        # Mock successful response
        mock_response = Mock()
        mock_response.content = BytesIO()
        self.test_image.save(mock_response.content, format="PNG")
        mock_response.content.seek(0)
        mock_response.content = mock_response.content.getvalue()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        img, name = self.loader.load("https://example.com/image.png")
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (100, 100))
        self.assertEqual(name, "image")

        # Test timeout
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
        with self.assertRaises(ValueError) as cm:
            self.loader.load("https://example.com/timeout.png")
        self.assertIn("Connection timed out", str(cm.exception))

        # Test connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        with self.assertRaises(ValueError) as cm:
            self.loader.load("https://example.com/error.png")
        self.assertIn("Connection failed", str(cm.exception))

    def test_output_formats(self):
        """Test all output formats using load_img function."""
        # Test PIL output
        result_pil = load_img(self.test_image, output_type="pil")
        self.assertIsInstance(result_pil, Image.Image)
        self.assertEqual(result_pil.size, (100, 100))

        # Test numpy output
        result_numpy = load_img(self.test_image, output_type="numpy")
        self.assertIsInstance(result_numpy, np.ndarray)
        self.assertEqual(result_numpy.shape[:2], (100, 100))

        # Test string (file path) output
        result_str = load_img(self.test_image, output_type="str")
        self.assertIsInstance(result_str, str)
        self.assertTrue(Path(result_str).exists())
        # Clean up the temporary file
        Path(result_str).unlink(missing_ok=True)

        # Test base64 output
        result_base64 = load_img(self.test_image, output_type="base64")
        self.assertIsInstance(result_base64, str)
        # Verify we can decode and load the base64 result
        img_from_base64 = load_img(result_base64)
        self.assertEqual(img_from_base64.size, (100, 100))

    def test_url_special_cases(self):
        """Test URL handling for special cases."""
        with patch("requests.Session.get") as mock_get:
            mock_response = Mock()
            mock_response.content = BytesIO()
            self.test_image.save(mock_response.content, format="PNG")
            mock_response.content.seek(0)
            mock_response.content = mock_response.content.getvalue()
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            # Test GitHub URL
            self.loader.load("https://github.com/user/repo/image.png")
            mock_get.assert_called_with(
                "https://github.com/user/repo/image.png?raw=true", timeout=ANY
            )

            # Test Google Drive URL
            self.loader.load("https://drive.google.com/file/d/123456/view")
            mock_get.assert_called_with(
                "https://drive.google.com/uc?id=123456", timeout=ANY
            )

            # Test Hugging Face URL
            self.loader.load("https://huggingface.co/repo/blob/main/image.png")
            mock_get.assert_called_with(
                "https://huggingface.co/repo/resolve/main/image.png", timeout=ANY
            )

            # Test HF shorthand URL
            self.loader.load("https://hf.co/repo/blob/main/image.png")
            mock_get.assert_called_with(
                "https://hf.co/repo/resolve/main/image.png", timeout=ANY
            )

    def test_invalid_inputs(self):
        """Test handling of invalid inputs."""
        # Test invalid input type
        with self.assertRaises(ValueError) as cm:
            self.loader.load("test", input_type="invalid")
        self.assertIn("Invalid input type", str(cm.exception))

        # Test invalid output type
        with self.assertRaises(ValueError) as cm:
            load_img(self.test_image, output_type="invalid")
        self.assertIn("Invalid output type", str(cm.exception))

        # Test corrupted image file
        corrupt_file = self.temp_dir / "corrupt.png"
        corrupt_file.write_bytes(b"not an image")
        with self.assertRaises(ValueError) as cm:
            self.loader.load(str(corrupt_file))
        self.assertIn("Failed to load image from file", str(cm.exception))

    def test_caching(self):
        """Test that caching works as expected."""
        # Test URL caching
        with patch("requests.Session.get") as mock_get:
            mock_response = Mock()
            mock_response.content = BytesIO()
            self.test_image.save(mock_response.content, format="PNG")
            mock_response.content.seek(0)
            mock_response.content = mock_response.content.getvalue()
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            # First call should make the request
            self.loader.load("https://example.com/test.png")
            self.assertEqual(mock_get.call_count, 1)

            # Second call should use cache
            self.loader.load("https://example.com/test.png")
            self.assertEqual(mock_get.call_count, 1)

        # Test file caching
        with patch.object(Image, "open", wraps=Image.open) as mock_open:
            # First call should open the file
            self.loader.load(str(self.test_file))
            self.assertEqual(mock_open.call_count, 1)

            # Second call should use cache
            self.loader.load(str(self.test_file))
            self.assertEqual(mock_open.call_count, 1)


if __name__ == "__main__":
    unittest.main()
