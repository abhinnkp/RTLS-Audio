import argparse
import sys
import os

from app.hardware.platform import PlatformDetector, MockPlatformDetector
from app.hardware.time_sync import SystemdTimeSyncManager, MockTimeSyncManager
from app.capture.audio_device import ALSAAudioDevice, MockAudioDevice
import signal

from app.recorder.recording_service import RecordingService
from app.storage.monitor import StorageMonitor
from app.lifecycle.session_manager import SessionManager
from app.config.config import ConfigLoader
from app.utils.logger import setup_logger

def get_detectors(use_mock: bool, config):
    if use_mock:
        return MockPlatformDetector(), MockAudioDevice(), MockTimeSyncManager(config)
    return PlatformDetector(), ALSAAudioDevice(), SystemdTimeSyncManager(config)

def cmd_status(args, config):
    platform_detector, audio_device, time_sync = get_detectors(args.mock, config)

    info = platform_detector.detect()

    print("RTLS+ Audio")
    print("-" * 25)
    print(f"Raspberry Pi: {info.pi_model if info.is_raspberry_pi else 'No'}")
    if info.pi_revision:
        print(f"Revision: {info.pi_revision}")
    print(f"Architecture: {info.cpu_architecture}")
    print(f"OS: {info.os_name}")
    print(f"Kernel: {info.kernel_version}")
    print(f"CPU cores: {info.cpu_cores}")
    print(f"CPU model: {info.cpu_model}")
    time_status = time_sync.get_status()
    print("\nTime:")
    print("-" * 25)
    print(f"Current system time: {time_status.current_time}")
    print(f"Time synchronization: {'synchronized' if time_status.is_synchronized else 'not synchronized'}")
    print(f"NTP enabled: {'yes' if time_status.ntp_enabled else 'no'}")
    print(f"NTP server: {time_status.configured_server}")

    print("\nAudio Devices:")
    print("-" * 25)

    devices = audio_device.list_devices()
    if not devices:
        print("No capture devices found.")
    else:
        for d in devices:
            print(f"Device {d.card_index}: {d.name}")
            if d.capabilities:
                print(f"  Channels: {d.capabilities.channels}")
                print(f"  Sample Rates: {d.capabilities.sample_rates}")

def cmd_audio_devices(args, config):
    _, audio_device, _ = get_detectors(args.mock, config)
    devices = audio_device.list_devices()
    print("\nAvailable ALSA Capture Devices:")
    print("-" * 35)
    if not devices:
        print("No capture devices found.")
    else:
        for d in devices:
            print(f"Device {d.card_index}: {d.name}")
            if d.capabilities:
                print(f"  Channels: {d.capabilities.channels}")
                print(f"  Sample Rates: {d.capabilities.sample_rates}")

def cmd_audio_test(args, config, logger):
    _, audio_device, _ = get_detectors(args.mock, config)
    recorder = RecordingService(audio_device, logger)

    # Use config as defaults if not explicitly provided
    sample_rate = args.rate if args.rate is not None else config.audio.sample_rate
    channels = args.channels if args.channels is not None else config.audio.channels
    device = args.device if args.device is not None else config.audio.device
    duration = args.duration if args.duration is not None else config.audio.recording_duration

    output_dir = args.output_dir if args.output_dir is not None else config.paths.data_dir

    print(f"Recording a {duration}-second test audio...")
    print(f"Using device: '{device}', Sample rate: {sample_rate}Hz, Channels: {channels}")

    result = recorder.record(
        output_dir=output_dir,
        duration_sec=duration,
        sample_rate=sample_rate,
        channels=channels,
        sample_width=config.audio.sample_width,
        device_name=device
    )

    if result.success:
        print("Recording successful.")
        print(f"Saved to: {result.output_path}")
        print(f"Captured {result.frames_captured} frames ({result.duration_captured:.2f}s).")
    else:
        print("Recording failed.")
        if result.error_message:
            print(f"Error: {result.error_message}")
        if result.frames_captured > 0:
            print(f"Partial capture: {result.frames_captured} frames saved to {result.output_path}")
        sys.exit(1)

def cmd_run(args, config, logger):
    _, audio_device, _ = get_detectors(args.mock, config)
    recorder = RecordingService(audio_device, logger)
    storage = StorageMonitor(config.storage, logger)
    manager = SessionManager(config, logger, recorder, storage)

    def sig_handler(signum, frame):
        logger.info(f"Received signal {signum}. Triggering graceful shutdown.")
        manager.shutdown()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    try:
        manager.run()
    except Exception as e:
        logger.critical(f"Fatal exception in SessionManager runloop: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="RTLS+ Audio CLI")
    parser.add_argument("--config", type=str, help="Path to config file", default=None)
    parser.add_argument("--mock", action="store_true", help="Use mock hardware for testing", default=os.environ.get("RTLS_MOCK", "0") == "1")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # run (Daemon)
    subparsers.add_parser("run", help="Start the continuous audio recording daemon.")

    # apply-config
    subparsers.add_parser("apply-config", help="Applies OS-level configuration (e.g. systemd-timesyncd NTP). May require root.")

    # status
    subparsers.add_parser("status", help="Print platform and audio status")

    # audio-devices
    subparsers.add_parser("audio-devices", help="List available ALSA capture devices")

    # audio-test
    audio_parser = subparsers.add_parser("audio-test", help="Capture a short test audio file")
    audio_parser.add_argument("--duration", type=int, default=None, help="Duration in seconds (defaults to config)")
    audio_parser.add_argument("--output-dir", type=str, default=None, help="Output directory path (defaults to config)")
    audio_parser.add_argument("--rate", type=int, default=None, help="Sample rate (defaults to config)")
    audio_parser.add_argument("--channels", type=int, default=None, help="Number of channels (defaults to config)")
    audio_parser.add_argument("--device", type=str, default=None, help="ALSA device name (defaults to config)")

    args = parser.parse_args()

    # Initialize basic config and logger
    config = ConfigLoader.load(args.config)
    logger = setup_logger(config.paths.log_dir, console_only=True)

    if args.command == "run":
        cmd_run(args, config, logger)
    elif args.command == "apply-config":
        _, _, time_sync = get_detectors(args.mock, config)
        time_sync.logger = logger # Enable logging for apply phase
        success = time_sync.apply_configuration()
        if not success:
            print("Failed to apply configuration. Root privileges may be required.")
            sys.exit(1)
        print("Configuration applied successfully.")
    elif args.command == "status":
        cmd_status(args, config)
    elif args.command == "audio-devices":
        cmd_audio_devices(args, config)
    elif args.command == "audio-test":
        cmd_audio_test(args, config, logger)

if __name__ == "__main__":
    main()
