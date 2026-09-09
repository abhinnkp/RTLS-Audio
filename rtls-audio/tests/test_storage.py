import unittest
from unittest.mock import MagicMock
from app.config.config import StorageConfig
from app.storage.monitor import StorageMonitor, StorageStatus

class MockStatVFS:
    def __init__(self, f_bavail, f_frsize, f_blocks, f_bfree):
        self.f_bavail = f_bavail
        self.f_frsize = f_frsize
        self.f_blocks = f_blocks
        self.f_bfree = f_bfree

class TestStorageMonitor(unittest.TestCase):
    def setUp(self):
        self.config = StorageConfig(minimum_free_mb=500, maximum_usage_percent=95)
        self.logger = MagicMock()

    def test_healthy_storage(self):
        # 1000MB free out of 10000MB (10% used, 90% free)
        mock_statvfs = lambda path: MockStatVFS(
            f_bavail=1000 * 1024, # blocks
            f_frsize=1024,        # bytes per block
            f_blocks=10000 * 1024,
            f_bfree=9000 * 1024
        )

        monitor = StorageMonitor(self.config, self.logger, statvfs_func=mock_statvfs)
        status = monitor.check_storage("/fake/path")

        self.assertTrue(status.can_record)
        self.assertEqual(status.free_mb, 1000)
        self.assertEqual(status.usage_percent, 10)

    def test_below_minimum_free_mb(self):
        # 400MB free (Below 500MB threshold) out of 10000MB
        mock_statvfs = lambda path: MockStatVFS(
            f_bavail=400 * 1024,
            f_frsize=1024,
            f_blocks=10000 * 1024,
            f_bfree=400 * 1024
        )

        monitor = StorageMonitor(self.config, self.logger, statvfs_func=mock_statvfs)
        status = monitor.check_storage("/fake/path")

        self.assertFalse(status.can_record)
        self.assertEqual(status.free_mb, 400)

    def test_above_maximum_usage_percent(self):
        # 600MB free (Above threshold), but on a tiny 620MB disk (96% utilized)
        mock_statvfs = lambda path: MockStatVFS(
            f_bavail=600 * 1024,
            f_frsize=1024,
            f_blocks=620 * 1024, # To get ~96% usage
            f_bfree=20 * 1024    # Used = 600, Total = 620 -> 96.7%
        )

        monitor = StorageMonitor(self.config, self.logger, statvfs_func=mock_statvfs)
        status = monitor.check_storage("/fake/path")

        self.assertFalse(status.can_record)
        self.assertEqual(status.usage_percent, 96)

    def test_smb_not_mounted(self):
        # Even if statvfs looks healthy, if smb is enabled but not mounted it should fail
        from app.config.config import SMBConfig
        config = StorageConfig(minimum_free_mb=500, maximum_usage_percent=95, smb=SMBConfig(enabled=True))

        mock_statvfs = lambda path: MockStatVFS(
            f_bavail=1000 * 1024, f_frsize=1024, f_blocks=10000 * 1024, f_bfree=9000 * 1024
        )

        monitor = StorageMonitor(config, self.logger, statvfs_func=mock_statvfs, ismount_func=lambda p: False)
        status = monitor.check_storage("/mnt/recordings")

        self.assertFalse(status.can_record)
        self.assertFalse(status.is_mounted)
        self.assertEqual(status.free_mb, 0)

    def test_smb_mounted_healthy(self):
        from app.config.config import SMBConfig
        config = StorageConfig(minimum_free_mb=500, maximum_usage_percent=95, smb=SMBConfig(enabled=True))

        mock_statvfs = lambda path: MockStatVFS(
            f_bavail=1000 * 1024, f_frsize=1024, f_blocks=10000 * 1024, f_bfree=9000 * 1024
        )

        monitor = StorageMonitor(config, self.logger, statvfs_func=mock_statvfs, ismount_func=lambda p: True)
        status = monitor.check_storage("/mnt/recordings")

        self.assertTrue(status.can_record)
        self.assertTrue(status.is_mounted)
        self.assertEqual(status.free_mb, 1000)

if __name__ == '__main__':
    unittest.main()
