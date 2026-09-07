import unittest
import tempfile
import os
import subprocess
from unittest.mock import patch

from app.config.config import AppConfig, TimeConfig, NTPConfig
from app.hardware.time_sync import MockTimeSyncManager, SystemdTimeSyncManager

class TestTimeSync(unittest.TestCase):
    def test_mock_time_sync_enabled_synced(self):
        config = AppConfig(time=TimeConfig(ntp=NTPConfig(enabled=True, server="10.0.0.2")))
        manager = MockTimeSyncManager(config, force_sync_status=True)
        status = manager.get_status()

        self.assertTrue(status.ntp_enabled)
        self.assertEqual(status.configured_server, "10.0.0.2")
        self.assertTrue(status.is_synchronized)
        self.assertTrue("T" in status.current_time) # Check ISO 8601 format roughly

    def test_mock_time_sync_enabled_unsynced(self):
        config = AppConfig(time=TimeConfig(ntp=NTPConfig(enabled=True, server="10.0.0.2")))
        manager = MockTimeSyncManager(config, force_sync_status=False)
        status = manager.get_status()

        self.assertTrue(status.ntp_enabled)
        self.assertFalse(status.is_synchronized)

    def test_mock_time_sync_disabled(self):
        config = AppConfig(time=TimeConfig(ntp=NTPConfig(enabled=False, server="10.0.0.2")))
        manager = MockTimeSyncManager(config, force_sync_status=True) # Even if forced true, if disabled, should be false
        status = manager.get_status()

        self.assertFalse(status.ntp_enabled)
        self.assertFalse(status.is_synchronized)

    @patch('app.hardware.time_sync.subprocess.run')
    def test_systemd_apply_creates_new_file(self, mock_subprocess):
        mock_subprocess.return_value = subprocess.CompletedProcess(args=[], returncode=0)
        config = AppConfig(time=TimeConfig(ntp=NTPConfig(enabled=True, server="10.5.1.1")))

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name

        os.remove(temp_path) # Ensure it doesn't exist to test creation logic

        try:
            manager = SystemdTimeSyncManager(config, timesyncd_conf_path=temp_path)
            success = manager.apply_configuration()
            self.assertTrue(success)

            with open(temp_path, 'r') as f:
                content = f.read()
            self.assertIn("[Time]", content)
            self.assertIn("NTP=10.5.1.1", content)

            mock_subprocess.assert_called_with(["systemctl", "restart", "systemd-timesyncd"], check=True, capture_output=True)

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @patch('app.hardware.time_sync.subprocess.run')
    def test_systemd_apply_replaces_existing(self, mock_subprocess):
        mock_subprocess.return_value = subprocess.CompletedProcess(args=[], returncode=0)
        config = AppConfig(time=TimeConfig(ntp=NTPConfig(enabled=True, server="10.5.2.2")))

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("[Time]\nNTP=old.server.local\nFallbackNTP=0.debian.pool.ntp.org\n")
            temp_path = f.name

        try:
            manager = SystemdTimeSyncManager(config, timesyncd_conf_path=temp_path)
            success = manager.apply_configuration()
            self.assertTrue(success)

            with open(temp_path, 'r') as f:
                content = f.read()
            self.assertIn("[Time]", content)
            self.assertIn("NTP=10.5.2.2", content)
            self.assertNotIn("old.server.local", content)
            self.assertIn("FallbackNTP=0.debian.pool.ntp.org", content) # Preserves other lines

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @patch('app.hardware.time_sync.subprocess.run')
    def test_systemd_apply_disabled(self, mock_subprocess):
        config = AppConfig(time=TimeConfig(ntp=NTPConfig(enabled=False, server="10.5.3.3")))

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("[Time]\n#NTP=\n")
            temp_path = f.name

        try:
            manager = SystemdTimeSyncManager(config, timesyncd_conf_path=temp_path)
            success = manager.apply_configuration()
            self.assertTrue(success) # Bypassing returns true

            # File should be completely untouched
            with open(temp_path, 'r') as f:
                content = f.read()
            self.assertNotIn("10.5.3.3", content)
            mock_subprocess.assert_not_called()

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == '__main__':
    unittest.main()
