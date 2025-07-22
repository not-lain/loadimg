import unittest
import tempfile
import os
from PIL import Image
from unittest.mock import patch, MagicMock
from loadimg.loadimg import main


class TestCLI(unittest.TestCase):
    @patch("loadimg.utils.requests.post")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_with_url_output_type(self, mock_args, mock_post):
        # Mock upload response
        mock_response = MagicMock()
        mock_response.text = '{"files": [{"url": "https://fake.uguu.se/fake.png"}]}'
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        mock_args.return_value = MagicMock(
            input=self.test_image_path, output_type="url", input_type="auto"
        )

        with patch("builtins.print") as mock_print:
            exit_code = main()
            self.assertEqual(exit_code, 0)
            mock_print.assert_called()
    def setUp(self):
        # Create a temporary test image
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_image_path = os.path.join(self.temp_dir.name, "test.png")
        test_image = Image.new("RGB", (100, 100), color="red")
        test_image.save(self.test_image_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("argparse.ArgumentParser.parse_args")
    def test_main_with_file_input(self, mock_args):
        # Test basic file input with default settings
        mock_args.return_value = MagicMock(
            input=self.test_image_path, output_type="ansi", input_type="auto"
        )

        with patch("builtins.print") as mock_print:
            exit_code = main()
            self.assertEqual(exit_code, 0)
            mock_print.assert_called()

    @patch("argparse.ArgumentParser.parse_args")
    def test_main_with_invalid_file(self, mock_args):
        # Test handling of non-existent file
        mock_args.return_value = MagicMock(
            input="nonexistent.jpg", output_type="ansi", input_type="auto"
        )

        with patch("builtins.print") as mock_print:
            exit_code = main()
            self.assertEqual(exit_code, 1)
            mock_print.assert_called()

    @patch("argparse.ArgumentParser.parse_args")
    def test_main_with_different_output_types(self, mock_args):
        # Test different output types
        output_types = ["ascii", "ansi", "base64", "str"]

        for output_type in output_types:
            mock_args.return_value = MagicMock(
                input=self.test_image_path, output_type=output_type, input_type="auto"
            )

            with patch("builtins.print") as mock_print:
                exit_code = main()
                self.assertEqual(exit_code, 0)
                mock_print.assert_called()

    def test_cli_argument_parsing(self):
        test_cases = [
            ["loadimg", self.test_image_path],
            ["loadimg", self.test_image_path, "--output-type", "ascii"],
            ["loadimg", self.test_image_path, "--input-type", "file"],
            [
                "loadimg",
                self.test_image_path,
                "--output-type",
                "ansi",
                "--input-type",
                "file",
            ],
        ]

        for args in test_cases:
            with patch("sys.argv", args), patch("builtins.print"), patch(
                "argparse.ArgumentParser._print_message"
            ), patch("sys.exit") as mock_exit:
                main()
                # Check that sys.exit wasn't called with an error code
                if mock_exit.called:
                    self.assertEqual(mock_exit.call_args[0][0], 0)

    def test_help_message(self):
        with patch("sys.argv", ["loadimg", "--help"]), patch(
            "argparse.ArgumentParser.print_help"
        ) as mock_help, patch("builtins.print"), patch("sys.exit"):
            try:
                main()
            except SystemExit:
                pass
            mock_help.assert_called_once()


if __name__ == "__main__":
    unittest.main()
