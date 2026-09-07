import unittest
from app.hardware.platform import MockPlatformDetector

class TestHardware(unittest.TestCase):
    def test_mock_platform_detector(self):
        detector = MockPlatformDetector(pi_model="Raspberry Pi 4", cpu_arch="aarch64", cores=4)
        info = detector.detect()

        self.assertTrue(info.is_raspberry_pi)
        self.assertEqual(info.pi_model, "Raspberry Pi 4")
        self.assertEqual(info.cpu_architecture, "aarch64")
        self.assertEqual(info.cpu_cores, 4)

if __name__ == '__main__':
    unittest.main()
