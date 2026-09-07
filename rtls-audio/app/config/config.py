import yaml
import os
from dataclasses import dataclass, field

@dataclass
class PathsConfig:
    data_dir: str = "/var/lib/rtls-audio"
    log_dir: str = "/var/log/rtls-audio"

@dataclass
class AudioConfig:
    device: str = "default"
    sample_rate: int = 48000
    channels: int = 2

@dataclass
class AppConfig:
    paths: PathsConfig = field(default_factory=PathsConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)

class ConfigLoader:
    @staticmethod
    def load(config_path: str = None) -> AppConfig:
        if config_path:
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Configuration file not found: {config_path}")

            try:
                with open(config_path, 'r') as f:
                    data = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML configuration: {e}")

            paths_data = data.get('paths', {})
            audio_data = data.get('audio', {})

            paths_config = PathsConfig(
                data_dir=paths_data.get('data_dir', "/var/lib/rtls-audio"),
                log_dir=paths_data.get('log_dir', "/var/log/rtls-audio")
            )

            audio_config = AudioConfig(
                device=audio_data.get('device', "default"),
                sample_rate=audio_data.get('sample_rate', 48000),
                channels=audio_data.get('channels', 2)
            )

            return AppConfig(paths=paths_config, audio=audio_config)

        return AppConfig()
