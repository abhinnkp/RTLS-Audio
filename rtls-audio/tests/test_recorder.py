import unittest
import os
import shutil
import wave
import logging
from app.capture.audio_device import MockAudioDevice
from app.recorder.recording_service import RecordingService

class TestRecorder(unittest.TestCase):
    def setUp(self):
        self.output_dir = "test_recordings"
        self.logger = logging.getLogger("test_recorder")
        self.device = MockAudioDevice()
        self.service = RecordingService(self.device, self.logger)

    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_successful_recording(self):
        result = self.service.record(
            output_dir=self.output_dir,
            duration_sec=1,
            sample_rate=16000,
            channels=2,
            sample_width=2,
            device_name="mock_generic"
        )

        self.assertTrue(result.success)
        self.assertIsNotNone(result.output_path)
        self.assertTrue(os.path.exists(result.output_path))
        self.assertEqual(result.frames_captured, 16000)
        self.assertIsNone(result.error_message)

        # Verify WAV metadata
        with wave.open(result.output_path, 'rb') as w:
            self.assertEqual(w.getnchannels(), 2)
            self.assertEqual(w.getsampwidth(), 2)
            self.assertEqual(w.getframerate(), 16000)
            self.assertEqual(w.getnframes(), 16000)

    def test_device_open_failure(self):
        result = self.service.record(
            output_dir=self.output_dir,
            duration_sec=1,
            device_name="mock_open_error"
        )

        self.assertFalse(result.success)
        self.assertIn("Failed to open audio device", result.error_message)
        self.assertEqual(result.frames_captured, 0)

    def test_zero_frame_capture(self):
        result = self.service.record(
            output_dir=self.output_dir,
            duration_sec=1,
            device_name="mock_zero_frame"
        )

        self.assertFalse(result.success)
        self.assertIn("Capture failed or zero frames read", result.error_message)
        self.assertEqual(result.frames_captured, 0)

        # Assert file was cleaned up
        if result.output_path:
            self.assertFalse(os.path.exists(result.output_path))

    def test_interrupted_read_error(self):
        result = self.service.record(
            output_dir=self.output_dir,
            duration_sec=2,
            sample_rate=1600,
            device_name="mock_read_error"
        )

        # mock_read_error triggers IOError after 5 reads (6 reads total before failure). 6 * 160 = 960 frames.
        self.assertFalse(result.success)
        self.assertIn("Error during audio capture", result.error_message)
        self.assertEqual(result.frames_captured, 960)

        # Assert partial file remains
        self.assertTrue(os.path.exists(result.output_path))
        with wave.open(result.output_path, 'rb') as w:
            self.assertEqual(w.getnframes(), 960)

    def test_filename_collision(self):
        result1 = self.service.record(
            output_dir=self.output_dir,
            duration_sec=0, # Fast fail to just get filename
            device_name="mock_zero_frame"
        )
        result2 = self.service.record(
            output_dir=self.output_dir,
            duration_sec=0,
            device_name="mock_zero_frame"
        )

        # Even if executed in same second, uuid ensures different paths
        self.assertNotEqual(result1.output_path, result2.output_path)

    def test_invalid_sample_width_rejection(self):
        result = self.service.record(
            output_dir=self.output_dir,
            duration_sec=1,
            sample_width=4
        )

        self.assertFalse(result.success)
        self.assertIn("Unsupported sample width", result.error_message)

if __name__ == '__main__':
    unittest.main()
