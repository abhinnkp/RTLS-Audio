import os
import abc
import subprocess
import datetime
from dataclasses import dataclass
from typing import Optional
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
    def apply_configuration(self) -> bool:
        """Applies the YAML NTP configuration to the OS"""
        pass

class SystemdTimeSyncManager(AbstractTimeSyncManager):
    def __init__(self, config: AppConfig, logger=None, timesyncd_conf_path: str = "/etc/systemd/timesyncd.conf"):
        self.config = config
        self.logger = logger
        self.timesyncd_conf_path = timesyncd_conf_path

    def apply_configuration(self) -> bool:
        if not self.config.time.ntp.enabled:
            if self.logger:
                self.logger.info("NTP is disabled in configuration. Bypassing timesyncd configuration.")
            return True

        server = self.config.time.ntp.server

        try:
            if not os.path.exists(self.timesyncd_conf_path):
                # Create the file safely if it's completely missing
                lines = []
            else:
                with open(self.timesyncd_conf_path, 'r') as f:
                    lines = f.readlines()

            new_lines = []
            in_time_section = False
            ntp_set = False
            found_time_section = False

            forbidden_pools = ["pool.ntp.org", "time.google.com", "time.windows.com", "time.apple.com"]

            for line in lines:
                stripped = line.strip()
                if stripped == "[Time]":
                    in_time_section = True
                    found_time_section = True
                    new_lines.append(line)
                elif in_time_section and stripped.startswith("NTP="):
                    if not ntp_set:
                        # Replace the first existing active NTP
                        new_lines.append(f"NTP={server}\n")
                        ntp_set = True
                    # If ntp_set is already True, we drop this line (removing duplicates)
                elif in_time_section and stripped.startswith("FallbackNTP="):
                    # Check if it contains public pools. If it does, discard it to prevent leak.
                    has_public_pool = any(pool in stripped.lower() for pool in forbidden_pools)
                    if not has_public_pool:
                        new_lines.append(line)
                elif in_time_section and stripped.startswith("#NTP="):
                    # Keep commented lines intact, we will insert real one
                    new_lines.append(line)
                elif in_time_section and stripped.startswith("["):
                    # We reached the next section
                    if not ntp_set:
                        # Insert right before the next section
                        new_lines.insert(-1, f"NTP={server}\n")
                        ntp_set = True
                    in_time_section = False
                    new_lines.append(line)
                else:
                    new_lines.append(line)

            if in_time_section and not ntp_set:
                new_lines.append(f"NTP={server}\n")
                ntp_set = True

            if not found_time_section:
                # Add [Time] section and NTP block at EOF if missing entirely
                new_lines.append("\n[Time]\n")
                new_lines.append(f"NTP={server}\n")

            with open(self.timesyncd_conf_path, 'w') as f:
                f.writelines(new_lines)

            subprocess.run(["systemctl", "restart", "systemd-timesyncd"], check=True, capture_output=True)

            if self.logger:
                self.logger.info(f"Applied NTP server {server} to timesyncd.")

            return True

        except PermissionError:
            if self.logger:
                self.logger.error(f"Permission denied modifying {self.timesyncd_conf_path}. Cannot apply NTP config.")
            return False
        except subprocess.CalledProcessError as e:
            if self.logger:
                self.logger.error(f"Failed to restart systemd-timesyncd: {e}")
            return False
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to apply NTP configuration: {e}")
            return False

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
