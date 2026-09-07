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

    def test_invalid_config_type(self):
        import tempfile
        import yaml

        test_config = {
            "audio": {"sample_rate": "not_an_int"}
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            yaml.dump(test_config, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValueError) as context:
                ConfigLoader.load(temp_path)
            self.assertIn("Invalid audio.sample_rate: must be a positive integer", str(context.exception))
        finally:
            os.remove(temp_path)

    def test_invalid_config_value(self):
        import tempfile
        import yaml

        test_config = {
            "audio": {"channels": -1}
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            yaml.dump(test_config, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValueError) as context:
                ConfigLoader.load(temp_path)
            self.assertIn("Invalid audio.channels: must be a positive integer", str(context.exception))
        finally:
            os.remove(temp_path)

    def test_invalid_ntp_server(self):
        import tempfile
        import yaml

        test_config = {
            "time": {"ntp": {"server": "pool.ntp.org"}}
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            yaml.dump(test_config, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValueError) as context:
                ConfigLoader.load(temp_path)
            self.assertIn("Public internet NTP servers are not permitted", str(context.exception))
        finally:
            os.remove(temp_path)

    def test_valid_ipv4_and_hostname_ntp_server(self):
        import tempfile
        import yaml

        test_config = {
            "time": {"ntp": {"server": "ntp.local.intranet"}}
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            yaml.dump(test_config, f)
            temp_path = f.name

        try:
            config = ConfigLoader.load(temp_path)
            self.assertEqual(config.time.ntp.server, "ntp.local.intranet")
        finally:
            os.remove(temp_path)

if __name__ == '__main__':
    unittest.main()
