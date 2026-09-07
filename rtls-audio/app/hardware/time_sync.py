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

    @abc.abstractmethod
    def apply_configuration(self):
        """Applies the YAML NTP configuration to the OS"""
        pass

class SystemdTimeSyncManager(AbstractTimeSyncManager):
    def __init__(self, config: AppConfig, logger=None):
        self.config = config
        self.logger = logger
        self.timesyncd_conf_path = "/etc/systemd/timesyncd.conf"

    def apply_configuration(self):
        if not self.config.time.ntp.enabled:
            if self.logger:
                self.logger.info("NTP is disabled in configuration. Bypassing timesyncd configuration.")
            return

        server = self.config.time.ntp.server

        try:
            # In a real Debian Trixie environment, we modify systemd-timesyncd.conf
            # and restart the service to apply the new local intranet NTP server.
            # We strictly replace the NTP= line under [Time].
            if not os.path.exists(self.timesyncd_conf_path):
                if self.logger:
                    self.logger.warning(f"Could not find {self.timesyncd_conf_path}. System may not use systemd-timesyncd.")
                return

            with open(self.timesyncd_conf_path, 'r') as f:
                lines = f.readlines()

            new_lines = []
            in_time_section = False
            ntp_set = False

            for line in lines:
                if line.strip().startswith("[Time]"):
                    in_time_section = True
                    new_lines.append(line)
                elif in_time_section and line.strip().startswith("NTP="):
                    new_lines.append(f"NTP={server}\n")
                    ntp_set = True
                elif in_time_section and line.strip().startswith("["):
                    # End of Time section
                    if not ntp_set:
                        # Insert before next section if it wasn't found
                        new_lines.insert(-1, f"NTP={server}\n")
                        ntp_set = True
                    in_time_section = False
                    new_lines.append(line)
                else:
                    new_lines.append(line)

            if in_time_section and not ntp_set:
                new_lines.append(f"NTP={server}\n")

            # Note: Writing requires root. In production, rtls-audio may need privileges
            # or a helper script with sudoers access to apply this.
            with open(self.timesyncd_conf_path, 'w') as f:
                f.writelines(new_lines)

            # Restart service
            subprocess.run(["systemctl", "restart", "systemd-timesyncd"], check=True, capture_output=True)

            if self.logger:
                self.logger.info(f"Applied NTP server {server} to timesyncd.")

        except PermissionError:
            if self.logger:
                self.logger.warning(f"Permission denied modifying {self.timesyncd_conf_path}. Cannot apply NTP config.")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to apply NTP configuration: {e}")

    def get_status(self) -> TimeSyncStatus:
        current_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        ntp_enabled = self.config.time.ntp.enabled
        configured_server = self.config.time.ntp.server
        is_synchronized = False

        if not ntp_enabled:
            return TimeSyncStatus(
                current_time=current_time,
                ntp_enabled=False,
                configured_server=configured_server,
                is_synchronized=False
            )

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
        self.applied = False

    def apply_configuration(self):
        self.applied = True

    def get_status(self) -> TimeSyncStatus:
        current_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return TimeSyncStatus(
            current_time=current_time,
            ntp_enabled=self.config.time.ntp.enabled,
            configured_server=self.config.time.ntp.server,
            is_synchronized=self.force_sync_status if self.config.time.ntp.enabled else False
        )
