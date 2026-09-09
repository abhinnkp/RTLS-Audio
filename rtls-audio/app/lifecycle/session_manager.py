import time
import logging
from threading import Event

from app.config.config import AppConfig
from app.recorder.recording_service import RecordingService
from app.storage.monitor import StorageMonitor

class SessionManagerState:
    IDLE = "IDLE"
    RECORDING = "RECORDING"
    RETRY_WAIT = "RETRY_WAIT"
    STORAGE_BLOCKED = "STORAGE_BLOCKED"
    SHUTTING_DOWN = "SHUTTING_DOWN"

class SessionManager:
    def __init__(self, config: AppConfig, logger: logging.Logger,
                 recording_service: RecordingService, storage_monitor: StorageMonitor,
                 sleep_func=time.sleep):
        self.config = config
        self.logger = logger
        self.recording_service = recording_service
        self.storage_monitor = storage_monitor
        self.sleep_func = sleep_func

        self.state = SessionManagerState.IDLE
        self.stop_event = Event()

    def run(self):
        self.logger.info("Starting autonomous continuous recording lifecycle.")
        self.state = SessionManagerState.IDLE

        while not self.stop_event.is_set():
            # 1. Check Storage
            storage_status = self.storage_monitor.check_storage(self.config.storage.recording_path)
            if not storage_status.can_record:
                if self.state != SessionManagerState.STORAGE_BLOCKED:
                    if not storage_status.is_mounted:
                        self.logger.critical(f"Storage blocked! SMB Mount Unavailable at {self.config.storage.recording_path}")
                    else:
                        self.logger.critical(
                            f"Storage blocked! Free MB: {storage_status.free_mb} (<{self.config.storage.minimum_free_mb}), "
                            f"Usage %: {storage_status.usage_percent} (>{self.config.storage.maximum_usage_percent}). Halting new recordings."
                        )
                    self.state = SessionManagerState.STORAGE_BLOCKED

                # Sleep-poll the disk safely avoiding a busy loop
                self._safe_sleep(10)
                continue

            # If we were blocked but now have space
            if self.state == SessionManagerState.STORAGE_BLOCKED:
                self.logger.info("Storage thresholds recovered. Resuming recording lifecycle.")

            # 2. Record segment
            self.state = SessionManagerState.RECORDING
            self.logger.info("Starting new recording segment.")

            def storage_check_cb():
                status = self.storage_monitor.check_storage(self.config.storage.recording_path)
                return status.can_record

            result = self.recording_service.record(
                output_dir=self.config.storage.recording_path,
                duration_sec=self.config.recording.segment_duration_sec,
                sample_rate=self.config.audio.sample_rate,
                channels=self.config.audio.channels,
                sample_width=self.config.audio.sample_width,
                device_name=self.config.audio.device,
                stop_event=self.stop_event,
                storage_check_callback=storage_check_cb,
                storage_check_interval_frames=self.config.audio.sample_rate * 5 # check every 5 seconds
            )

            # 3. Check shutdown before logging failures
            if self.stop_event.is_set() or result.status == "SHUTDOWN":
                self.state = SessionManagerState.SHUTTING_DOWN
                break

            # 4. Check result and recover if needed
            if result.success:
                self.logger.info(f"Segment completed cleanly: {result.output_path} ({result.duration_captured:.2f}s)")
                self.state = SessionManagerState.IDLE
            else:
                self.logger.error(f"Recording failed. Status: {result.status}. Result: {result.error_message}. Path: {result.output_path}")

                # Distinguish between STORAGE error and ALSA error
                if result.status == "STORAGE_ERROR":
                    self.state = SessionManagerState.STORAGE_BLOCKED
                else:
                    self.state = SessionManagerState.RETRY_WAIT
                    self.logger.info(f"Entering retry backoff for {self.config.recording.retry_backoff_sec} seconds.")
                    self._safe_sleep(self.config.recording.retry_backoff_sec)

        self.state = SessionManagerState.SHUTTING_DOWN
        self.logger.info("Session manager runloop has gracefully terminated.")

    def shutdown(self):
        """Signals the session manager and active recording loops to halt."""
        self.logger.info("Shutdown signal received. Intercepting recording lifecycle...")
        self.state = SessionManagerState.SHUTTING_DOWN
        self.stop_event.set()

    def _safe_sleep(self, duration: int):
        """Sleeps in short bursts to quickly abort if a shutdown is requested."""
        for _ in range(int(duration * 10)):
            if self.stop_event.is_set():
                break
            self.sleep_func(0.1)
