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
        self.assertIn("Raspberry Pi Zero 2 W", output)
        self.assertIn("Mock ReSpeaker 2-Mic", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_audio_test_mock(self, mock_stdout):
        test_args = ["rtls-audio", "--mock", "audio-test", "--duration", "1", "--output", "cli_test.wav"]
        with patch.object(sys, 'argv', test_args):
            main()

        output = mock_stdout.getvalue()
        self.assertIn("Recording successful", output)

        import os
        if os.path.exists("cli_test.wav"):
            os.remove("cli_test.wav")

if __name__ == '__main__':
    unittest.main()
