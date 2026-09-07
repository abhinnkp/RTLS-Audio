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
The `RecordingService` is the canonical and sole path for audio captures. It leverages the `AbstractAudioStream` (`capture/audio_device.py`), consuming audio in safely chunked blocks. This prevents large memory allocations, ensuring stable execution on memory-constrained SBC hardware (e.g. Pi 3B+).

- **Format**: Milestone 2 supports 16-bit PCM only.
- **Failures & Partials**: The service differentiates between a clean success, a zero-frame failure (which triggers automatic deletion of the empty WAV), and an interrupted partial failure (which safely retains the partial WAV). Genuine IO errors during ALSA `read()` are cleanly propagated and tracked.
- **Filenames**: Generated deterministically using `YYYYMMDD_HHMMSS_UTC_<UUID>.wav` to prevent any possibility of intra-second collisions.

## 8. Time Synchronization
The application requires accurate time for recording timestamps but operates on isolated intranets. It avoids all custom Python NTP implementations. The configuration validates local NTP IP/Hostnames and writes them into `/etc/systemd/timesyncd.conf`, relying directly on OS-level daemon capabilities (`systemd-timesyncd`). Public internet pools (`pool.ntp.org`) are explicitly blocked. All WAV generation utilizes timezone-aware `UTC` timestamps mapping strictly to the synchronized OS clock.

## 9. Deferred Assumptions (Milestone 2)
- **Production Device Mapping:** Exact ReSpeaker hardware identifiers, mapping configurations, and required channel widths are not explicitly hard-coded; they remain managed via config mapping until production integration testing provides authoritative settings.
- **Audio Profile:** We defer selecting the final sample rate, VAD sensitivity, and spatial processing configuration to future milestones.
- **System Services:** systemd unit creation and hardening are left skeletonized until core processing pipelines are defined.
- **AI/ML & Cloud:** ML enhancement integrations and external uploads (SMB/FTP) are entirely out of scope for this milestone.
