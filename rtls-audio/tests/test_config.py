import os
import unittest
from app.config.config import ConfigLoader

class TestConfig(unittest.TestCase):
    def test_default_config(self):
        config = ConfigLoader.load(None)
        self.assertEqual(config.paths.data_dir, "/var/lib/rtls-audio")
        self.assertEqual(config.audio.sample_rate, 48000)

    def test_custom_config(self):
        import tempfile
        import yaml

        test_config = {
            "paths": {"data_dir": "/tmp/data"},
            "audio": {"channels": 1}
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            yaml.dump(test_config, f)
            temp_path = f.name

        try:
            config = ConfigLoader.load(temp_path)
            self.assertEqual(config.paths.data_dir, "/tmp/data")
            self.assertEqual(config.audio.channels, 1)
        finally:
            os.remove(temp_path)

if __name__ == '__main__':
    unittest.main()
