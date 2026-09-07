import abc
import subprocess
import datetime
from dataclasses import dataclass
from app.config.config import AppConfig

@dataclass
class TimeSyncStatus:
    current_time: str
    ntp_enabled: bool
    configured_server: str
    is_synchronized: bool

class AbstractTimeSyncManager(abc.ABC):
    @abc.abstractmethod
    def get_status(self) -> TimeSyncStatus:
        pass

class SystemdTimeSyncManager(AbstractTimeSyncManager):
    def __init__(self, config: AppConfig):
        self.config = config

    def get_status(self) -> TimeSyncStatus:
        current_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        ntp_enabled = self.config.time.ntp.enabled
        configured_server = self.config.time.ntp.server
        is_synchronized = False

        # In a real environment, we'd parse timedatectl status
        try:
            result = subprocess.run(["timedatectl", "show"], capture_output=True, text=True, check=True)
            for line in result.stdout.splitlines():
                if line.startswith("NTPSynchronized="):
                    val = line.split("=")[1].strip().lower()
                    if val == "yes":
                        is_synchronized = True
        except Exception:
            # If timedatectl fails (e.g. not systemd, or permissions issue), assume unsynchronized
            is_synchronized = False

        return TimeSyncStatus(
            current_time=current_time,
            ntp_enabled=ntp_enabled,
            configured_server=configured_server,
            is_synchronized=is_synchronized
        )

class MockTimeSyncManager(AbstractTimeSyncManager):
    def __init__(self, config: AppConfig, force_sync_status: bool = True):
        self.config = config
        self.force_sync_status = force_sync_status

    def get_status(self) -> TimeSyncStatus:
        current_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return TimeSyncStatus(
            current_time=current_time,
            ntp_enabled=self.config.time.ntp.enabled,
            configured_server=self.config.time.ntp.server,
            is_synchronized=self.force_sync_status if self.config.time.ntp.enabled else False
        )
