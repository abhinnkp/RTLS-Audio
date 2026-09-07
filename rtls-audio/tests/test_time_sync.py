import unittest
from app.config.config import AppConfig, TimeConfig, NTPConfig
from app.hardware.time_sync import MockTimeSyncManager

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

if __name__ == '__main__':
    unittest.main()
