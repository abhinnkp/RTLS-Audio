import unittest
import os
import wave
from app.capture.audio_device import MockAudioDevice

class TestAudio(unittest.TestCase):
    def test_mock_audio_list_devices(self):
        device = MockAudioDevice()
        devices = device.list_devices()

        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0].name, "Mock ReSpeaker 2-Mic")
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

if __name__ == '__main__':
    unittest.main()
