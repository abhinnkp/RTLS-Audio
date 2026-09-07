# RTLS+ Audio Architecture

This document describes the foundational architecture of the RTLS+ Audio application as established in Milestone 2.

**Project Scope Constraint**: The application is strictly **AUDIO-ONLY**. There are no camera, V4L2, RTLS video processing, or computer vision subsystems integrated or planned.

## 1. Application Layers
The application is structured into loosely coupled modules:
- **CLI / Entrypoint**: Exposes commands to the user (e.g., `rtls-audio status`, `rtls-audio audio-test`).
- **Core Abstractions**:
  - `hardware/`: Detects the underlying OS and Raspberry Pi characteristics.
  - `capture/`: Interfaces with ALSA to list capabilities and provide abstracted stream reading logic.
  - `recorder/`: Orchestrates the stream reading and safe chunked encoding into standard WAV format.
- **Configuration & Utilities**: YAML-based config parsing (`config/`) and structured logging (`utils/`).

## 2. Hardware Abstraction Boundary
The core logic must never directly read from `/proc` or run commands like `uname` manually. Instead, it queries `app.hardware.platform.PlatformDetector.detect()`, which returns a standardized `PlatformInfo` object. This makes it trivial to mock hardware for testing and enables unified support for Pi 3B+, Pi 4, and Pi 5.

## 3. Audio Abstraction Boundary
ALSA APIs are isolated behind `AbstractAudioDevice`. `app.capture.audio_device.ALSAAudioDevice` handles true device discovery via `pyalsaaudio`. A `MockAudioDevice` provides functional equivalence for non-hardware environments like CI pipelines.

**Note on Capabilities:** Reliable reporting of supported channels and sample rates purely by probing PCMs without opening the devices is complicated in standard ALSA wrappers. Our capability discovery intentionally leaves detailed capability maps as `None` when running on physical hardware unless it can be seamlessly resolved; we avoid fragile CLI parsing.

## 4. Configuration Boundary
Configuration is defined strictly through `app.config.config.ConfigLoader`, generating a typed `AppConfig` object. Paths are inherently dynamic so developers can run tests without `root` using local folders (e.g., `./logs/` rather than `/var/log/rtls-audio/`).

## 5. Dependency Injection & Testing Strategy
Where necessary, core functions accept detector instances rather than instantiating the real ones directly. Environment variables or CLI flags (`--mock`) inject `MockPlatformDetector` and `MockAudioDevice` allowing the entire test suite to pass on x86_64 machines lacking ALSA configurations or ReSpeaker HATs.

## 6. Raspberry Pi 3B+/4/5 Compatibility
Rather than using global configuration for "is_pi_3", capabilities will later be queried dynamically through profiles based on CPU core count, available RAM, and CPU architecture exposed via `PlatformInfo`.

## 7. Recording Architecture & WAV Generation
The `RecordingService` leverages the `AbstractAudioStream` (`capture/audio_device.py`), consuming audio in safely chunked blocks. This design fundamentally prevents large memory allocations, ensuring stable execution on memory-constrained SBC hardware (e.g. Pi 3B+) across extended recordings. It cleanly tracks failed devices, disrupted streams, and handles zero-byte wave file cleanup.

## 8. Deferred Assumptions (Milestone 2)
- **Production Device Mapping:** Exact ReSpeaker hardware identifiers, mapping configurations, and required channel widths are not explicitly hard-coded; they remain managed via config mapping until production integration testing provides authoritative settings.
- **Audio Profile:** We defer selecting the final sample rate, VAD sensitivity, and spatial processing configuration to future milestones.
- **System Services:** systemd unit creation and hardening are left skeletonized until core processing pipelines are defined.
- **AI/ML & Cloud:** ML enhancement integrations and external uploads (SMB/FTP) are entirely out of scope for this milestone.
