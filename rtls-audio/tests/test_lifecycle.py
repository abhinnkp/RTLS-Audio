import unittest
from unittest.mock import MagicMock, call
import os
import shutil
from threading import Event

from app.config.config import AppConfig, RecordingConfig, StorageConfig, AudioConfig, PathsConfig
from app.lifecycle.session_manager import SessionManager, SessionManagerState
from app.storage.monitor import StorageStatus

class TestLifecycle(unittest.TestCase):
    def setUp(self):
        self.config = AppConfig(
            paths=PathsConfig(data_dir="test_lifecycle_data"),
            recording=RecordingConfig(segment_duration_sec=2, retry_backoff_sec=1),
            storage=StorageConfig(minimum_free_mb=500, maximum_usage_percent=95),
            audio=AudioConfig()
        )
        self.logger = MagicMock()
        self.recording_service = MagicMock()
        self.storage_monitor = MagicMock()
        self.sleep_func = MagicMock()

        self.manager = SessionManager(
            config=self.config,
            logger=self.logger,
            recording_service=self.recording_service,
            storage_monitor=self.storage_monitor,
            sleep_func=self.sleep_func
        )

        if not os.path.exists(self.config.paths.data_dir):
            os.makedirs(self.config.paths.data_dir)

    def tearDown(self):
        if os.path.exists(self.config.paths.data_dir):
            shutil.rmtree(self.config.paths.data_dir)

    def test_continuous_recording_loop(self):
        # Allow storage check to pass twice, then trigger shutdown so it doesn't infinite loop
        self.storage_monitor.check_storage.return_value = StorageStatus(free_mb=1000, usage_percent=50, can_record=True)

        # Simulate recording result
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.output_path = "mock_file.wav"
        mock_result.duration_captured = 2.0

        # We will shut down on the second call to RecordingService
        def side_effect_record(*args, **kwargs):
            if self.recording_service.record.call_count == 2:
                self.manager.shutdown()
            return mock_result

        self.recording_service.record.side_effect = side_effect_record

        self.manager.run()

        self.assertEqual(self.manager.state, SessionManagerState.SHUTTING_DOWN)
        self.assertEqual(self.recording_service.record.call_count, 2)
        self.storage_monitor.check_storage.assert_called()

    def test_storage_blocked_behavior(self):
        # Disk full, should enter sleep poll loop
        self.storage_monitor.check_storage.return_value = StorageStatus(free_mb=100, usage_percent=99, can_record=False)

        # Stop loop after 3 checks
        def side_effect_sleep(*args, **kwargs):
            if self.storage_monitor.check_storage.call_count == 3:
                self.manager.shutdown()

        self.sleep_func.side_effect = side_effect_sleep

        self.manager.run()

        self.assertEqual(self.manager.state, SessionManagerState.SHUTTING_DOWN)
        # Verify recording was never called
        self.recording_service.record.assert_not_called()
        self.logger.critical.assert_called()

    def test_alsa_recoverable_failure_backoff(self):
        self.storage_monitor.check_storage.return_value = StorageStatus(free_mb=1000, usage_percent=50, can_record=True)

        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error_message = "Mocked ALSA Read Error"

        # Fail first time, succeed second time, then shutdown
        def side_effect_record(*args, **kwargs):
            if self.recording_service.record.call_count == 1:
                return mock_result
            else:
                self.manager.shutdown()
                mock_success = MagicMock()
                mock_success.success = True
                return mock_success

        self.recording_service.record.side_effect = side_effect_record

        self.manager.run()

        # Sleep should have been called due to RETRY_WAIT
        self.sleep_func.assert_called()
        self.assertEqual(self.recording_service.record.call_count, 2)

if __name__ == '__main__':
    unittest.main()
