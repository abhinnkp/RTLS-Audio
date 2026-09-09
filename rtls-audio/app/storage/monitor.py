import os
import logging
from dataclasses import dataclass
from typing import Callable

from app.config.config import StorageConfig

@dataclass
class StorageStatus:
    free_mb: int
    usage_percent: int
    can_record: bool
    is_mounted: bool = True
    error_message: str = None

class StorageMonitor:
    def __init__(self, config: StorageConfig, logger: logging.Logger,
                 statvfs_func: Callable = os.statvfs,
                 ismount_func: Callable = os.path.ismount):
        self.config = config
        self.logger = logger
        self.statvfs_func = statvfs_func
        self.ismount_func = ismount_func

    def check_storage(self, directory_path: str) -> StorageStatus:
        try:
            if self.config.smb.enabled:
                if not self.ismount_func(directory_path):
                    msg = f"Configured SMB recording path {directory_path} is not mounted. Denying local fallback."
                    self.logger.error(msg)
                    return StorageStatus(
                        free_mb=0, usage_percent=100, can_record=False, is_mounted=False, error_message=msg
                    )

            # Ensure path exists before checking, or check its parent if not created yet
            check_path = directory_path
            if not os.path.exists(check_path):
                # We check root as fallback or assume creating dir will fail later
                check_path = os.path.dirname(directory_path) or "/"

            st = self.statvfs_func(check_path)

            # Block size * available blocks / 1024 / 1024
            free_mb = int((st.f_bavail * st.f_frsize) / 1048576)

            # (Total blocks - Free blocks) / Total blocks
            total_blocks = st.f_blocks
            if total_blocks > 0:
                used_blocks = total_blocks - st.f_bfree
                usage_percent = int((used_blocks / total_blocks) * 100)
            else:
                usage_percent = 100

            can_record = (free_mb >= self.config.minimum_free_mb) and (usage_percent < self.config.maximum_usage_percent)

            return StorageStatus(
                free_mb=free_mb,
                usage_percent=usage_percent,
                can_record=can_record,
                is_mounted=True
            )

        except Exception as e:
            msg = f"Failed to read storage statistics for {directory_path}: {e}"
            self.logger.error(msg)
            return StorageStatus(
                free_mb=0,
                usage_percent=100,
                can_record=False,
                is_mounted=False,
                error_message=msg
            )
