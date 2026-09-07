# Milestone 3: Production Recording Lifecycle & Management Plan

## 1. Objective
Establish a fully autonomous, unattended, and continuous audio recording lifecycle that operates flawlessly on Pi 3B+/4/5 hardware. This layer will run on top of the rock-solid Milestone 1 and 2 abstractions, bringing session management, safe segmenting, storage bounds, and systemd integration to life.

## 2. Functional Requirements
- **Continuous Operation**: Seamlessly trigger recordings, bound by configurable duration limits, looping automatically to establish 24/7 capture where required.
- **Recording Segmentation**: Divide continuous sessions into distinct WAV segments (e.g., max 10 minutes per file) to prevent giant monolithic file vulnerabilities.
- **Storage Management**: Actively monitor disk space. Suspend capture, log critically, and safely close files if storage falls below a configurable safe threshold.
- **Resilience & Recovery**: Trap temporary device disconnects or ALSA crashes, implement backoff-and-retry loops, and ensure the system recovers autonomously without full OS reboots.
- **Graceful Shutdown**: Intercept SIGINT/SIGTERM to cleanly truncate running WAV streams and release ALSA locks before the process exits.
- **Service Integration**: Formalize the `systemd` deployment profiles (`rtls-audio.service`).

## 3. Proposed Architecture Changes
- **New Module (`app/lifecycle/session_manager.py`)**: Responsible for orchestrating the `RecordingService`. It will manage the infinite recording loop, tracking segmentation intervals and monitoring disk space boundaries.
- **New Module (`app/storage/monitor.py`)**: A lightweight disk utility to query partition availability and compute percentage usage against YAML-configured boundaries.
- **Signal Handling**: Integrate `signal.signal` callbacks into the main runloop to flag a `stop_event`, prompting the `SessionManager` to flush the active `RecordingService` stream.

## 4. Files/Modules to Create or Modify
- `app/lifecycle/session_manager.py` (New)
- `app/storage/monitor.py` (New)
- `app/cli.py` (Add a `daemon` or `run` command)
- `systemd/rtls-audio.service` (Flesh out the skeleton)
- `tests/test_lifecycle.py` (New)
- `tests/test_storage.py` (New)

## 5. Configuration Changes
Expand `config.yaml` (`AppConfig`):
```yaml
storage:
  minimum_free_mb: 500
  maximum_usage_percent: 95
recording:
  segment_duration_sec: 600
  retry_backoff_sec: 5
```

## 6. Systemd / Service Changes
Write the definitive `/etc/systemd/system/rtls-audio.service`.
- `Restart=always` and `RestartSec=10`
- `ExecStart=/usr/local/bin/rtls-audio run`
- Setup isolated non-root user targets where ALSA `audio` group permissions allow it.

## 7. Error and Recovery Strategy
- If `RecordingService` returns `success=False` (e.g., IO Read Error, Device Drop):
  - Log error critically.
  - Sleep for `retry_backoff_sec`.
  - Attempt to reinitialize the audio stream and commence the next segment.
- If Disk Space hits the limit:
  - Stop the loop. Log critically.
  - Sleep polling the disk until space is freed (or wait for watchdog restart).

## 8. Testing Strategy
- Use `MockAudioStream` to trigger `IOError` midway through a continuous loop, asserting that `SessionManager` recovers and opens a *new* mock file after a backoff.
- Mock `os.statvfs` to simulate an artificially full disk, asserting that the daemon gracefully denies recording requests.
- Verify `SIGINT` cleanly breaks the infinite loop in a sandbox thread.

## 9. Documentation Changes
- Add `docs/lifecycle.md` documenting continuous operation schemas, recovery mechanisms, and `systemd` configurations.
- Update `README.md` with instructions on installing/starting the daemon.

## 10. Acceptance Criteria
- A `rtls-audio run` command exists and successfully orchestrates segmented recordings.
- Subsystem gracefully recovers from mock ALSA crashes.
- Subsystem gracefully halts on mock disk-full events.
- System strictly avoids all camera/video logic.

## 11. Decisions/Clarifications
- *Retention Policies*: Unless explicit rotation (auto-deleting oldest files) is mandated now, Milestone 3 will *stop* recording when full rather than destroying history. Is rotation required for M3? (Assuming NO for now, but easily expandable).
- *VAD*: Does Voice Activity Detection boundary integration belong in M3, or an M4? (Assuming M3 builds the continuous segmenter, and VAD simply gates the segmenter in M4).
