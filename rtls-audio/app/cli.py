import argparse
import sys
import os

from app.hardware.platform import PlatformDetector, MockPlatformDetector
from app.capture.audio_device import ALSAAudioDevice, MockAudioDevice
from app.config.config import ConfigLoader
from app.utils.logger import setup_logger

def get_detectors(use_mock: bool):
    if use_mock:
        return MockPlatformDetector(), MockAudioDevice()
    return PlatformDetector(), ALSAAudioDevice()

def cmd_status(args):
    platform_detector, audio_device = get_detectors(args.mock)

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

def cmd_audio_test(args, config):
    _, audio_device = get_detectors(args.mock)

    # Use config as defaults if not explicitly provided
    sample_rate = args.rate if args.rate is not None else config.audio.sample_rate
    channels = args.channels if args.channels is not None else config.audio.channels
    device = args.device if args.device is not None else config.audio.device

    print(f"Recording a {args.duration}-second test audio to {args.output}...")
    print(f"Using device: '{device}', Sample rate: {sample_rate}Hz, Channels: {channels}")

    success = audio_device.capture_test_audio(
        duration_sec=args.duration,
        filepath=args.output,
        sample_rate=sample_rate,
        channels=channels,
        device=device
    )

    if success:
        print("Recording successful.")
    else:
        print("Recording failed.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="RTLS+ Audio CLI")
    parser.add_argument("--config", type=str, help="Path to config file", default=None)
    parser.add_argument("--mock", action="store_true", help="Use mock hardware for testing", default=os.environ.get("RTLS_MOCK", "0") == "1")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    subparsers.add_parser("status", help="Print platform and audio status")

    # audio-test
    audio_parser = subparsers.add_parser("audio-test", help="Capture a short test audio file")
    audio_parser.add_argument("--duration", type=int, default=3, help="Duration in seconds")
    audio_parser.add_argument("--output", type=str, default="test_output.wav", help="Output file path")
    audio_parser.add_argument("--rate", type=int, default=None, help="Sample rate (defaults to config)")
    audio_parser.add_argument("--channels", type=int, default=None, help="Number of channels (defaults to config)")
    audio_parser.add_argument("--device", type=str, default=None, help="ALSA device name (defaults to config)")

    args = parser.parse_args()

    # Initialize basic config and logger
    config = ConfigLoader.load(args.config)
    setup_logger(config.paths.log_dir, console_only=True)

    if args.command == "status":
        cmd_status(args)
    elif args.command == "audio-test":
        cmd_audio_test(args, config)

if __name__ == "__main__":
    main()
