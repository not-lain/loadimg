import unittest
import os
import tempfile
import numpy as np
from PIL import Image
from loadimg import load_imgs

class TestMultipleImages(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_imgs_from_directory(self):
        # Create separate directory for multiple image tests
        multi_test_dir = os.path.join(self.temp_dir.name, "multi_tests")
        os.makedirs(multi_test_dir)
        
        # Create multiple test images
        test_images = []
        for i in range(3):
            img_path = os.path.join(multi_test_dir, f"multi_test_{i}.png")
            test_image = Image.new("RGB", (100, 100), color=f"#{i*20:02x}0000")
            test_image.save(img_path)
            test_images.append(img_path)

        results = load_imgs(multi_test_dir, output_type="pil", glob_pattern="multi_test_*.png")
        self.assertEqual(len(results), 3)
        self.assertTrue(all(isinstance(img, Image.Image) for img in results.values()))

        results = load_imgs(multi_test_dir, output_type="numpy", glob_pattern="multi_test_*.png")
        self.assertTrue(all(isinstance(img, np.ndarray) for img in results.values()))

    def test_load_imgs_from_list(self):
        list_test_dir = os.path.join(self.temp_dir.name, "list_tests")
        os.makedirs(list_test_dir)
        
        img_paths = []
        for i in range(2):
            img_path = os.path.join(list_test_dir, f"list_test_{i}.png")
            test_image = Image.new("RGB", (50, 50), color="red")
            test_image.save(img_path)
            img_paths.append(img_path)

        results = load_imgs(img_paths, output_type="pil")
        self.assertEqual(len(results), 2)
        self.assertTrue(all(isinstance(img, Image.Image) for img in results.values()))

    def test_load_imgs_error_handling(self):
        bad_paths = ["nonexistent1.jpg", "nonexistent2.jpg"]
        results = load_imgs(bad_paths, output_type="pil")
        self.assertEqual(len(results), 0)

        valid_path = os.path.join(self.temp_dir.name, "valid.png")
        Image.new("RGB", (50, 50), color="blue").save(valid_path)
        mixed_paths = [valid_path, "nonexistent.jpg"]
        results = load_imgs(mixed_paths, output_type="pil")
        self.assertEqual(len(results), 1)

    def test_load_imgs_with_glob(self):
        glob_test_dir = os.path.join(self.temp_dir.name, "glob_tests")
        os.makedirs(glob_test_dir)
        
        Image.new("RGB", (50, 50), color="red").save(
            os.path.join(glob_test_dir, "glob_test1.png"))
        Image.new("RGB", (50, 50), color="blue").save(
            os.path.join(glob_test_dir, "glob_test2.jpg"))
        Image.new("RGB", (50, 50), color="green").save(
            os.path.join(glob_test_dir, "glob_test3.png"))

        results = load_imgs(glob_test_dir, glob_pattern="glob_test*.png")
        self.assertEqual(len(results), 2)

        results = load_imgs(glob_test_dir, glob_pattern="glob_test*.jpg")
        self.assertEqual(len(results), 1)

    def test_load_imgs_parallel_processing(self):
        parallel_test_dir = os.path.join(self.temp_dir.name, "parallel_tests")
        os.makedirs(parallel_test_dir)
        
        num_images = 10
        for i in range(num_images):
            img_path = os.path.join(parallel_test_dir, f"parallel_test_{i}.png")
            test_image = Image.new("RGB", (50, 50), color="purple")
            test_image.save(img_path)

        for workers in [1, 2, 4]:
            results = load_imgs(parallel_test_dir, max_workers=workers, glob_pattern="parallel_test_*.png")
            self.assertEqual(len(results), num_images)

if __name__ == "__main__":
    unittest.main()
