# RTLS+ Audio

RTLS+ Audio is a production-oriented audio recording application designed for Raspberry Pi devices, primarily targeting the Raspberry Pi 3B+, Raspberry Pi 4, and Raspberry Pi 5.

## Project Structure
- `app/`: Core application source code
- `tests/`: Unit tests utilizing mocked interfaces for cross-platform validation
- `tools/`: Diagnostic and utility scripts
- `systemd/`: systemd service configuration skeletons
- `config/`: Configuration files and templates
- `scripts/`: Assorted build/run scripts
- `docs/`: Project architecture and documentation

## Milestone 1 Setup and Testing
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

# Uses mocked hardware interfaces (useful on development machines)
rtls-audio --mock status
```

To test capturing audio:
```bash
rtls-audio --mock audio-test --duration 2 --output mock_test.wav
```
