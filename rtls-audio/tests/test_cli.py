import unittest
import sys
from io import StringIO
from unittest.mock import patch
from app.cli import main

class TestCLI(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    def test_status_mock(self, mock_stdout):
        test_args = ["rtls-audio", "--mock", "status"]
        with patch.object(sys, 'argv', test_args):
            main()

        output = mock_stdout.getvalue()
        self.assertIn("Raspberry Pi", output)
        self.assertIn("Mock Generic Capture Device 0", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_audio_devices_mock(self, mock_stdout):
        test_args = ["rtls-audio", "--mock", "audio-devices"]
        with patch.object(sys, 'argv', test_args):
            main()

        output = mock_stdout.getvalue()
        self.assertIn("Available ALSA Capture Devices", output)
        self.assertIn("Mock Generic Capture Device 0", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_audio_test_mock(self, mock_stdout):
        test_args = ["rtls-audio", "--mock", "audio-test", "--duration", "1", "--output-dir", "cli_test_dir"]
        with patch.object(sys, 'argv', test_args):
            main()

        output = mock_stdout.getvalue()
        self.assertIn("Recording successful", output)
        self.assertIn("Sample rate: 48000Hz", output) # Assuming default config is used

        import os
        import shutil
        if os.path.exists("cli_test_dir"):
            shutil.rmtree("cli_test_dir")

    @patch('sys.stdout', new_callable=StringIO)
    def test_audio_test_mock_with_args(self, mock_stdout):
        test_args = ["rtls-audio", "--mock", "audio-test", "--duration", "1", "--output-dir", "cli_test_dir", "--rate", "16000", "--channels", "1", "--device", "mock_device"]
        with patch.object(sys, 'argv', test_args):
            main()

        output = mock_stdout.getvalue()
        self.assertIn("Recording successful", output)
        self.assertIn("Sample rate: 16000Hz", output)
        self.assertIn("Channels: 1", output)
        self.assertIn("Using device: 'mock_device'", output)

        import os
        import shutil
        if os.path.exists("cli_test_dir"):
            shutil.rmtree("cli_test_dir")

if __name__ == '__main__':
    unittest.main()
