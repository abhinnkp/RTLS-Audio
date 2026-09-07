# RTLS+ Audio Architecture

This document describes the foundational architecture of the RTLS+ Audio application as established in Milestone 1.

## 1. Application Layers
The application is structured into loosely coupled modules:
- **CLI / Entrypoint**: Exposes commands to the user (e.g., `rtls-audio status`, `rtls-audio audio-test`).
- **Core Abstractions**:
  - `hardware/`: Detects the underlying OS and Raspberry Pi characteristics.
  - `capture/`: Interfaces with ALSA to list capabilities and pull raw PCM frames.
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

## 7. Deferred Assumptions (Milestone 1)
- **Audio Profile:** We defer selecting the final sample rate, VAD sensitivity, and spatial processing configuration to future milestones.
- **System Services:** systemd unit creation and hardening are left skeletonized until core processing pipelines are defined.
- **AI/ML Pipelines:** ML enhancement integrations are entirely out of scope for this milestone.
