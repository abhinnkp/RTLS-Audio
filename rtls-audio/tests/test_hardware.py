import unittest
from app.hardware.platform import MockPlatformDetector

class TestHardware(unittest.TestCase):
    def test_mock_platform_detector_pi_3(self):
        detector = MockPlatformDetector(pi_model="Raspberry Pi 3 Model B Plus Rev 1.3", cpu_arch="aarch64", cores=4)
        info = detector.detect()
        self.assertTrue(info.is_raspberry_pi)
        self.assertEqual(info.pi_model, "Raspberry Pi 3 Model B Plus Rev 1.3")
        self.assertEqual(info.cpu_architecture, "aarch64")
        self.assertEqual(info.cpu_cores, 4)
        self.assertEqual(info.cpu_model, "Cortex-A53")
        self.assertEqual(info.os_name, "Debian GNU/Linux 13 (trixie)")

    def test_mock_platform_detector_pi_4(self):
        detector = MockPlatformDetector(pi_model="Raspberry Pi 4 Model B Rev 1.5", cpu_arch="aarch64", cores=4)
        info = detector.detect()
        self.assertTrue(info.is_raspberry_pi)
        self.assertEqual(info.pi_model, "Raspberry Pi 4 Model B Rev 1.5")
        self.assertEqual(info.cpu_cores, 4)
        self.assertEqual(info.cpu_model, "Cortex-A72")
        self.assertEqual(info.os_name, "Debian GNU/Linux 13 (trixie)")

    def test_mock_platform_detector_pi_5(self):
        detector = MockPlatformDetector(pi_model="Raspberry Pi 5 Model B Rev 1.0", cpu_arch="aarch64", cores=4)
        info = detector.detect()
        self.assertTrue(info.is_raspberry_pi)
        self.assertEqual(info.pi_model, "Raspberry Pi 5 Model B Rev 1.0")
        self.assertEqual(info.cpu_cores, 4)
        self.assertEqual(info.cpu_model, "Cortex-A76")
        self.assertEqual(info.os_name, "Debian GNU/Linux 13 (trixie)")

if __name__ == '__main__':
    unittest.main()
