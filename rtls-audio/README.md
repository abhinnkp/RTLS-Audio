# RTLS+ Audio

RTLS+ Audio is a production-oriented AUDIO-ONLY recording application designed for Raspberry Pi devices, primarily targeting the Raspberry Pi 3B+, Raspberry Pi 4, and Raspberry Pi 5. (Note: No camera integration exists or will be implemented).

**Note on Network Environment**: This device is designed for isolated Intranet installations. It operates without internet access and strictly does **not** rely on public internet NTP servers (e.g. `pool.ntp.org`). Instead, local intranet NTP servers are provided via YAML configuration. The application directly applies these settings to the OS (`systemd-timesyncd`) eliminating custom/fragile Python NTP logic and blocking internet fallbacks.

## Project Structure
- `app/`: Core application source code (hardware detection, ALSA audio, recording service)
- `tests/`: Unit tests utilizing mocked interfaces for cross-platform validation
- `tools/`: Diagnostic and utility scripts
- `systemd/`: systemd service configuration skeletons
- `config/`: Configuration files and templates
- `scripts/`: Assorted build/run scripts
- `docs/`: Project architecture and documentation

## Milestone 2 Setup and Testing
This project leverages `pyproject.toml` for standard packaging. To initialize:

```bash
# Optional: create a venv
python3 -m venv venv && source venv/bin/activate

# Install the package and dependencies
pip install -e .
```

To run the unit tests (which execute with mock devices and do not require ALSA or root):
```bash
python -m unittest discover tests
```

## Running CLI Diagnostics
To query platform info and available ALSA capture devices:
```bash
# Uses real hardware (requires ALSA)
rtls-audio status
rtls-audio audio-devices

# Uses mocked hardware interfaces (useful on development machines)
rtls-audio --mock status
rtls-audio --mock audio-devices
```

To test capturing audio through the recording service (which generates timestamped files):
```bash
rtls-audio --mock audio-test --duration 2 --output-dir ./recordings
```
