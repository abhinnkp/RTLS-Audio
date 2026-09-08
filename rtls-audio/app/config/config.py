import yaml
import os
from dataclasses import dataclass, field

@dataclass
class PathsConfig:
    data_dir: str = "/var/lib/rtls-audio"
    log_dir: str = "/var/log/rtls-audio"
    config_dir: str = "/etc/rtls-audio"

@dataclass
class AudioConfig:
    device: str = "default"
    sample_rate: int = 48000
    channels: int = 2
    sample_width: int = 2
    recording_duration: int = 3

@dataclass
class StorageConfig:
    minimum_free_mb: int = 500
    maximum_usage_percent: int = 95

@dataclass
class RecordingConfig:
    segment_duration_sec: int = 600
    retry_backoff_sec: int = 5

@dataclass
class NTPConfig:
    enabled: bool = True
    server: str = "10.0.0.1"

@dataclass
class TimeConfig:
    ntp: NTPConfig = field(default_factory=NTPConfig)

@dataclass
class AppConfig:
    paths: PathsConfig = field(default_factory=PathsConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    time: TimeConfig = field(default_factory=TimeConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    recording: RecordingConfig = field(default_factory=RecordingConfig)

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
            time_data = data.get('time', {})
            ntp_data = time_data.get('ntp', {})
            storage_data = data.get('storage', {})
            recording_data = data.get('recording', {})

            paths_config = PathsConfig(
                data_dir=paths_data.get('data_dir', "/var/lib/rtls-audio"),
                log_dir=paths_data.get('log_dir', "/var/log/rtls-audio"),
                config_dir=paths_data.get('config_dir', "/etc/rtls-audio")
            )

            audio_config = AudioConfig(
                device=audio_data.get('device', "default"),
                sample_rate=audio_data.get('sample_rate', 48000),
                channels=audio_data.get('channels', 2),
                sample_width=audio_data.get('sample_width', 2),
                recording_duration=audio_data.get('recording_duration', 3)
            )

            time_config = TimeConfig(
                ntp=NTPConfig(
                    enabled=ntp_data.get('enabled', True),
                    server=ntp_data.get('server', "10.0.0.1")
                )
            )

            storage_config = StorageConfig(
                minimum_free_mb=storage_data.get('minimum_free_mb', 500),
                maximum_usage_percent=storage_data.get('maximum_usage_percent', 95)
            )

            recording_config = RecordingConfig(
                segment_duration_sec=recording_data.get('segment_duration_sec', 600),
                retry_backoff_sec=recording_data.get('retry_backoff_sec', 5)
            )

            config = AppConfig(paths=paths_config, audio=audio_config, time=time_config, storage=storage_config, recording=recording_config)
            ConfigLoader.validate(config)
            return config

        return AppConfig()

    @staticmethod
    def validate(config: AppConfig):
        if not isinstance(config.paths.data_dir, str):
            raise ValueError(f"Invalid paths.data_dir: must be a string, got {type(config.paths.data_dir)}")
        if not isinstance(config.paths.log_dir, str):
            raise ValueError(f"Invalid paths.log_dir: must be a string, got {type(config.paths.log_dir)}")
        if not isinstance(config.paths.config_dir, str):
            raise ValueError(f"Invalid paths.config_dir: must be a string, got {type(config.paths.config_dir)}")

        if not isinstance(config.audio.device, str):
            raise ValueError(f"Invalid audio.device: must be a string, got {type(config.audio.device)}")

        if not isinstance(config.audio.sample_rate, int) or config.audio.sample_rate <= 0:
            raise ValueError(f"Invalid audio.sample_rate: must be a positive integer, got {config.audio.sample_rate}")

        if not isinstance(config.audio.channels, int) or config.audio.channels <= 0:
            raise ValueError(f"Invalid audio.channels: must be a positive integer, got {config.audio.channels}")

        if not isinstance(config.audio.sample_width, int) or config.audio.sample_width != 2:
            raise ValueError(f"Invalid audio.sample_width: only 16-bit PCM (sample_width=2) is currently supported, got {config.audio.sample_width}")

        if not isinstance(config.audio.recording_duration, int) or config.audio.recording_duration <= 0:
            raise ValueError(f"Invalid audio.recording_duration: must be a positive integer, got {config.audio.recording_duration}")

        if not isinstance(config.time.ntp.enabled, bool):
            raise ValueError(f"Invalid time.ntp.enabled: must be a boolean, got {type(config.time.ntp.enabled)}")

        if not isinstance(config.time.ntp.server, str) or not config.time.ntp.server.strip():
            raise ValueError(f"Invalid time.ntp.server: must be a non-empty string, got {config.time.ntp.server}")

        import re
        import ipaddress

        server = config.time.ntp.server.strip()
        is_valid_ip = False
        try:
            ipaddress.ip_address(server)
            is_valid_ip = True
        except ValueError:
            is_valid_ip = False

        if not is_valid_ip:
            # Fallback to strict regex for valid hostnames
            hostname_regex = re.compile(
                r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*'
                r'([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$'
            )
            if not hostname_regex.match(server):
                raise ValueError(f"Invalid time.ntp.server: must be a valid IPv4, IPv6, or hostname, got {server}")

        # Ensure it's not silently using a public pool if it accidentally slipped in
        forbidden_pools = ["pool.ntp.org", "time.google.com", "time.windows.com", "time.apple.com"]
        if any(pool in server.lower() for pool in forbidden_pools):
            raise ValueError(f"Invalid time.ntp.server: Public internet NTP servers are not permitted ({server})")

        if not isinstance(config.storage.minimum_free_mb, int) or config.storage.minimum_free_mb < 0:
            raise ValueError(f"Invalid storage.minimum_free_mb: must be a non-negative integer, got {config.storage.minimum_free_mb}")

        if not isinstance(config.storage.maximum_usage_percent, int) or not (0 <= config.storage.maximum_usage_percent <= 100):
            raise ValueError(f"Invalid storage.maximum_usage_percent: must be an integer between 0 and 100, got {config.storage.maximum_usage_percent}")

        if not isinstance(config.recording.segment_duration_sec, int) or config.recording.segment_duration_sec <= 0:
            raise ValueError(f"Invalid recording.segment_duration_sec: must be a positive integer, got {config.recording.segment_duration_sec}")

        if not isinstance(config.recording.retry_backoff_sec, int) or config.recording.retry_backoff_sec < 0:
            raise ValueError(f"Invalid recording.retry_backoff_sec: must be a non-negative integer, got {config.recording.retry_backoff_sec}")
