import unittest
import logging
from app.hardware.mixer import MockAudioMixer, ALSAMixer

class TestAudioMixer(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger("test_mixer")

    def test_mock_mixer(self):
        mixer = MockAudioMixer(self.logger)

        # Initial is -1
        self.assertEqual(mixer.get_pga_gain(), -1)

        # Successful set
        success = mixer.set_pga_gain(25)
        self.assertTrue(success)
        self.assertEqual(mixer.get_pga_gain(), 25)

        # Simulated failure
        success = mixer.set_pga_gain(-999)
        self.assertFalse(success)
        # Should not update value if failed
        self.assertEqual(mixer.get_pga_gain(), 25)

if __name__ == '__main__':
    unittest.main()
