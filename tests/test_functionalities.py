import unittest
import os
import tempfile
import numpy as np
from PIL import Image
import base64
from unittest.mock import patch, MagicMock

from loadimg import load_img, load_imgs
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

    def test_load_imgs_from_directory(self):
        # Create multiple test images
        test_images = []
        for i in range(3):
            img_path = os.path.join(self.temp_dir.name, f"test_{i}.png")
            test_image = Image.new("RGB", (100, 100), color=f"#{i*20:02x}0000")
            test_image.save(img_path)
            test_images.append(img_path)

        # Test loading from directory
        results = load_imgs(self.temp_dir.name, output_type="pil", glob_pattern="*.png")
        self.assertEqual(len(results), 3)
        self.assertTrue(all(isinstance(img, Image.Image) for img in results.values()))

        # Test different output types
        results = load_imgs(self.temp_dir.name, output_type="numpy")
        self.assertTrue(all(isinstance(img, np.ndarray) for img in results.values()))

        results = load_imgs(self.temp_dir.name, output_type="base64")
        self.assertTrue(all(isinstance(img, str) and img.startswith("data:image/") 
                          for img in results.values()))

    def test_load_imgs_from_list(self):
        # Create test images
        img_paths = []
        for i in range(2):
            img_path = os.path.join(self.temp_dir.name, f"list_test_{i}.png")
            test_image = Image.new("RGB", (50, 50), color="red")
            test_image.save(img_path)
            img_paths.append(img_path)

        # Test loading from list
        results = load_imgs(img_paths, output_type="pil")
        self.assertEqual(len(results), 2)
        self.assertTrue(all(isinstance(img, Image.Image) for img in results.values()))

    def test_load_imgs_error_handling(self):
        # Test with non-existent files
        bad_paths = ["nonexistent1.jpg", "nonexistent2.jpg"]
        results = load_imgs(bad_paths, output_type="pil")
        self.assertEqual(len(results), 0)

        # Test with mixed valid and invalid paths
        valid_path = os.path.join(self.temp_dir.name, "valid.png")
        Image.new("RGB", (50, 50), color="blue").save(valid_path)
        mixed_paths = [valid_path, "nonexistent.jpg"]
        results = load_imgs(mixed_paths, output_type="pil")
        self.assertEqual(len(results), 1)

    def test_load_imgs_with_glob(self):
        # Create test images with different extensions
        Image.new("RGB", (50, 50), color="red").save(
            os.path.join(self.temp_dir.name, "test1.png"))
        Image.new("RGB", (50, 50), color="blue").save(
            os.path.join(self.temp_dir.name, "test2.jpg"))
        Image.new("RGB", (50, 50), color="green").save(
            os.path.join(self.temp_dir.name, "test3.png"))

        # Test glob pattern
        results = load_imgs(self.temp_dir.name, glob_pattern="*.png")
        self.assertEqual(len(results), 2)

        results = load_imgs(self.temp_dir.name, glob_pattern="*.jpg")
        self.assertEqual(len(results), 1)

    def test_load_imgs_parallel_processing(self):
        # Create many test images to test parallel processing
        num_images = 10
        for i in range(num_images):
            img_path = os.path.join(self.temp_dir.name, f"parallel_test_{i}.png")
            test_image = Image.new("RGB", (50, 50), color="purple")
            test_image.save(img_path)

        # Test with different numbers of workers
        for workers in [1, 2, 4]:
            results = load_imgs(self.temp_dir.name, max_workers=workers)
            self.assertEqual(len(results), num_images)

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
