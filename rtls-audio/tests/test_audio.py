import unittest
import os
import wave
from app.capture.audio_device import MockAudioDevice

class TestAudio(unittest.TestCase):
    def test_mock_audio_list_devices(self):
        device = MockAudioDevice()
        devices = device.list_devices()

        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0].name, "Mock Generic Capture Device 0")
        self.assertIn(16000, devices[0].capabilities.sample_rates)

    def test_mock_audio_capture(self):
        device = MockAudioDevice()
        filepath = "test_capture.wav"

        try:
            success = device.capture_test_audio(duration_sec=1, filepath=filepath, sample_rate=16000, channels=2)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(filepath))

            with wave.open(filepath, 'rb') as w:
                self.assertEqual(w.getnchannels(), 2)
                self.assertEqual(w.getframerate(), 16000)
                # 1 second of audio at 16000Hz = 16000 frames
                self.assertEqual(w.getnframes(), 16000)
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_mock_audio_capture_invalid(self):
        device = MockAudioDevice()
        filepath = "test_capture_invalid.wav"

        # duration = 0 should return False
        success = device.capture_test_audio(duration_sec=0, filepath=filepath)
        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
