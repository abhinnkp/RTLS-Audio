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

if __name__ == '__main__':
    unittest.main()
