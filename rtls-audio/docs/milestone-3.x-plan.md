# Milestone 3.x: Production Deployment & Audio Hardware Configuration

## 1. Objective
Establish an idempotent setup utility that automates the deployment of RTLS+ Audio onto a Master SD image for the Pi 3B+/4/5. Alongside installation logic, introduce application-level configuration for the ReSpeaker hardware PGA (Programmable Gain Amplifier) without mixing hardware configuration logic into the `RecordingService`. Maintain the strictly offline, AUDIO-ONLY constraints without regressing M1, M2, or M3.

## 2. Functional Requirements
- **Production Setup Tool**: A script or module establishing users (`rtlsaudio`), groups (`audio`), directories (`/etc`, `/var/lib`, `/var/log`), systemd services, and configuration blueprints. It must be idempotent.
- **PGA Configuration**: Expose `audio.mixer.pga_gain_db` in `config.yaml`.
- **ALSA Mixer Abstraction**: A dedicated `AudioMixer` abstraction wrapping real ALSA commands to apply PGA settings and returning actual gain states if accessible.
- **Hardware Initialization**: PGA gain must be set *once* during application initialization (in the `SessionManager` or startup loop), not per-segment or within `RecordingService`.
- **Diagnostics Expansion**: `rtls-audio status` must be updated to report the configured PGA, application version, storage statuses, and active audio topologies.
- **Master Clones & Documentation**: Update documentation explicitly mapping the difference between Master preparations, cloning phases, and per-device configuration.

## 3. Proposed Architecture Changes
- **New Module (`app/hardware/mixer.py`)**: Defines `AbstractAudioMixer`, `ALSAMixer`, and `MockAudioMixer` for safe dependency injection.
- **New Installer Script (`scripts/install.sh`)**: A bash script orchestrating the OS-level mutations for the Master image creation. It will not destroy old recordings or configurations if run redundantly.
- **CLI/Status Additions**: `app/cli.py` will inject `MockAudioMixer` for test modes, reporting PGA details in `status`.

## 4. Files/Modules to Create or Modify
- `scripts/install.sh` (New)
- `app/hardware/mixer.py` (New)
- `app/config/config.py` (Add `MixerConfig`)
- `app/cli.py` (Wire up `AudioMixer` to `cmd_run` and `cmd_status`)
- `tests/test_mixer.py` (New)
- `tests/test_config.py` (Update for MixerConfig)
- `README.md` (Update Developer vs Master install)
- `docs/deployment.md` (New)

## 5. Configuration Changes
Expand `config.yaml` (`AppConfig`):
```yaml
audio:
  device: "default"
  sample_rate: 48000
  channels: 2
  sample_width: 2
  recording_duration: 3
  mixer:
    pga_gain_db: 25
```
Validation ensures `pga_gain_db` is a valid integer/float.

## 6. Installer Safety & Systemd Changes
- `install.sh` checks for Python 3.11+, establishes `rtlsaudio` user, ensures `audio` group mappings.
- Does NOT touch `/var/lib/rtls-audio/recordings` natively avoiding destructive operations.
- Backs up `config.yaml` to `config.yaml.bak` if overwriting.
- Provides flags or instructions for manual daemon reloads.

## 7. Error and Recovery Strategy
- **Mixer Unavailable**: If ALSA mixer cannot find the requested control, it logs an error clearly and refuses to start the recording runloop (prevents silent failures with wrong gain).

## 8. Testing Strategy
- `test_config.py` will assert default PGA gain is 25, validating bounds where necessary.
- `test_mixer.py` will use `MockAudioMixer` to mock ALSA controls.
- Ensure `rtls-audio --mock status` prints the PGA settings.
- Tests remain rootless, hardware independent, and without Pi devices.

## 9. Documentation Changes
- Create `docs/deployment.md` covering Master Pi prep, setup verification, log cleaning, and the clone logic mapping out per-device configurations.

## 10. Acceptance Criteria
- PGA is configured via YAML, isolated into an `AudioMixer` abstraction, and applied once on start.
- `install.sh` acts idempotently, avoiding destructive user/file operations while laying down systemd topologies securely.
- Tests pass locally.
- Diagnostics print the PGA and versioning gracefully.
- AUDIO-ONLY constraint is preserved.
