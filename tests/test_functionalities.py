import unittest
import os
import tempfile
import numpy as np
from PIL import Image
import base64
from unittest.mock import patch, MagicMock

from loadimg import load_img
from loadimg.utils import starts_with, download_image, isBase64


class TestImageLoader(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sample_image_path = os.path.join(self.temp_dir.name, "sample.png")
        self.sample_image = Image.new("RGB", (100, 100), color="red")
        self.sample_image.save(self.sample_image_path)
        self.sample_numpy_array = np.array(self.sample_image)

        with open(self.sample_image_path, "rb") as image_file:
            self.sample_base64 = base64.b64encode(image_file.read()).decode("utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_img_from_file(self):
        # Existing tests
        img = load_img(self.sample_image_path, output_type="pil")
        self.assertIsInstance(img, Image.Image)

        img = load_img(self.sample_image_path, output_type="numpy")
        self.assertIsInstance(img, np.ndarray)

        img = load_img(self.sample_image_path, output_type="str")
        self.assertTrue(os.path.exists(img))

        img = load_img(self.sample_image_path, output_type="base64")
        self.assertTrue(img.startswith("data:image/png;base64,"))

        # New ASCII/ANSI tests
        ascii_art = load_img(self.sample_image_path, output_type="ascii")
        self.assertIsInstance(ascii_art, str)
        self.assertGreater(len(ascii_art), 0)
        self.assertIn("\n", ascii_art)

        ansi_art = load_img(self.sample_image_path, output_type="ansi")
        self.assertIsInstance(ansi_art, str)
        self.assertGreater(len(ansi_art), 0)
        self.assertIn("\x1b[48;2;", ansi_art)
        self.assertIn("\x1b[0m", ansi_art)

    def test_load_img_from_base64(self):
        # Existing tests
        img = load_img(f"data:image/png;base64,{self.sample_base64}", output_type="pil")
        self.assertIsInstance(img, Image.Image)

        img = load_img(
            f"data:image/png;base64,{self.sample_base64}", output_type="numpy"
        )
        self.assertIsInstance(img, np.ndarray)

        img = load_img(f"data:image/png;base64,{self.sample_base64}", output_type="str")
        self.assertTrue(os.path.exists(img))

        img = load_img(
            f"data:image/png;base64,{self.sample_base64}", output_type="base64"
        )
        self.assertTrue(img.startswith("data:image/png;base64,"))

        # New ASCII/ANSI tests
        ascii_art = load_img(
            f"data:image/png;base64,{self.sample_base64}", output_type="ascii"
        )
        self.assertIsInstance(ascii_art, str)
        self.assertGreater(len(ascii_art), 0)

        ansi_art = load_img(
            f"data:image/png;base64,{self.sample_base64}", output_type="ansi"
        )
        self.assertIn("\x1b[48;2;", ansi_art)
        self.assertIn("\x1b[0m", ansi_art)

    def test_load_img_from_numpy(self):
        # Existing tests
        img = load_img(self.sample_numpy_array, output_type="pil")
        self.assertIsInstance(img, Image.Image)

        img = load_img(self.sample_numpy_array, output_type="numpy")
        self.assertIsInstance(img, np.ndarray)

        img = load_img(self.sample_numpy_array, output_type="str")
        self.assertTrue(os.path.exists(img))

        img = load_img(self.sample_numpy_array, output_type="base64")
        self.assertTrue(img.startswith("data:image/png;base64,"))

        # New ASCII/ANSI tests
        ascii_art = load_img(self.sample_numpy_array, output_type="ascii")
        self.assertGreater(len(ascii_art), 100)

        ansi_art = load_img(self.sample_numpy_array, output_type="ansi")
        self.assertIn("48;2;", ansi_art)

    def test_load_img_from_pil(self):
        # Existing tests
        img = load_img(self.sample_image, output_type="pil")
        self.assertIsInstance(img, Image.Image)

        img = load_img(self.sample_image, output_type="numpy")
        self.assertIsInstance(img, np.ndarray)

        img = load_img(self.sample_image, output_type="str")
        self.assertTrue(os.path.exists(img))

        img = load_img(self.sample_image, output_type="base64")
        self.assertTrue(img.startswith("data:image/png;base64,"))

        # New ASCII/ANSI tests
        ascii_art = load_img(self.sample_image, output_type="ascii")
        self.assertTrue(ascii_art.count("\n") >= 50)

        ansi_art = load_img(self.sample_image, output_type="ansi")
        self.assertTrue(ansi_art.count("\x1b[0m") >= 50)

    @patch("requests.get")
    def test_load_img_from_url(self, mock_get):
        # Mock setup
        mock_response = MagicMock()
        mock_response.content = open(self.sample_image_path, "rb").read()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Existing tests
        img = load_img("https://example.com/sample.png", output_type="pil")
        self.assertIsInstance(img, Image.Image)

        img = load_img("https://example.com/sample.png", output_type="numpy")
        self.assertIsInstance(img, np.ndarray)

        img = load_img("https://example.com/sample.png", output_type="str")
        self.assertTrue(os.path.exists(img))

        img = load_img("https://example.com/sample.png", output_type="base64")
        self.assertTrue(img.startswith("data:image/png;base64,"))

        # New ASCII/ANSI tests
        ascii_art = load_img("https://example.com/sample.png", output_type="ascii")
        self.assertIsInstance(ascii_art, str)
        self.assertGreater(len(ascii_art), 0)

        ansi_art = load_img("https://example.com/sample.png", output_type="ansi")
        self.assertIn("\x1b[48;2;", ansi_art)

    # Existing utility tests remain unchanged
    def test_starts_with(self):
        self.assertTrue(starts_with("github", "https://github.com/user/repo"))
        self.assertTrue(starts_with("github", "github.com/user/repo"))
        self.assertFalse(starts_with("github", "https://example.com"))

    @patch("requests.get")
    def test_download_image(self, mock_get):
        mock_response = MagicMock()
        mock_response.content = open(self.sample_image_path, "rb").read()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        img = download_image("https://example.com/sample.png")
        self.assertIsInstance(img, Image.Image)

    def test_isBase64(self):
        self.assertTrue(isBase64(self.sample_base64))
        self.assertFalse(isBase64("not a base64 string"))


if __name__ == "__main__":
    unittest.main()
