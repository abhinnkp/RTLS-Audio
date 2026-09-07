# Milestone 3: Production Recording Lifecycle & Management Plan

## 1. Objective
Establish a fully autonomous, unattended, and continuous audio recording lifecycle that operates flawlessly on Pi 3B+/4/5 hardware. This layer will run on top of the rock-solid Milestone 1 and 2 abstractions, bringing session management, safe segmenting, storage bounds, and systemd integration to life, while remaining strictly AUDIO-ONLY.

## 2. Functional Requirements
- **Continuous Operation**: Seamlessly trigger recordings, bound by configurable segment duration limits, looping automatically to establish 24/7 capture where required.
- **Recording Segmentation**: Divide continuous sessions into distinct WAV segments based on `recording.segment_duration_sec`. Every completed segment must have a unique filename, correct WAV metadata, and be cleanly closed before the next starts, strictly utilizing the existing `RecordingService`.
- **Storage Management**: Actively monitor disk space. If storage falls below a configurable safe threshold, stop starting new recordings, log critically, and continue monitoring without deleting existing recordings. Ensure future retention policies can be added without redesigning the architecture. Handle disk exhaustion gracefully mid-recording, ensuring the partial WAV remains valid.
- **Resilience & Recovery**: Clearly distinguish between recoverable runtime failures (which `SessionManager` retries internally with `retry_backoff_sec`) and fatal unhandled process failures (where the application exits cleanly and `systemd` `Restart=always` takes over). Avoid busy loops and competing retry mechanisms.
- **Graceful Shutdown**: Intercept SIGINT/SIGTERM to stop the active capture cleanly, finalize the WAV header, preserve already captured audio, close the ALSA stream and file, release resources, and exit cleanly.
- **Service Integration**: Formalize the `systemd` deployment profile (`rtls-audio.service`) to run as a dedicated non-root service account, documenting required group and directory permissions.

## 3. Proposed Architecture Changes
- **New Module (`app/lifecycle/session_manager.py`)**: Orchestrates the `RecordingService`. Manages the infinite recording loop, tracking segmentation intervals, monitoring disk space boundaries, handling graceful shutdowns via an injected stop event, and performing internal backoffs for recoverable errors.
- **New Module (`app/storage/monitor.py`)**: A lightweight disk utility to query partition availability and compute percentage usage against YAML-configured boundaries, injected into the `SessionManager`.

## 4. Files/Modules to Create or Modify
- `app/lifecycle/session_manager.py` (New)
- `app/storage/monitor.py` (New)
- `app/cli.py` (Add a `run` or `daemon` command)
- `systemd/rtls-audio.service` (Flesh out the skeleton)
- `tests/test_lifecycle.py` (New)
- `tests/test_storage.py` (New)
- `docs/lifecycle.md` (New)

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
*Note: `segment_duration_sec` dictates continuous recording chunks and is separate from the `audio-test` duration.*

## 6. Systemd / Service Changes
Write the definitive `/etc/systemd/system/rtls-audio.service`.
- Dependencies: Start after required filesystem/storage/audio dependencies. No internet or NTP-sync-success requirement.
- Restart Policy: `Restart=always` and `RestartSec=10`
- Execution: `ExecStart=/usr/local/bin/rtls-audio run`
- Security: Run as a non-root user. Document the necessary `audio` group permissions, and read/write permissions for config, data, and log directories.

## 7. Error and Recovery Strategy
- **Disk Exhaustion Mid-Recording**: The `RecordingService` handles the write error, finalizes the partial WAV, and reports it as partial/failed. The `SessionManager` then detects the low storage state and halts future segments.
- **Low Storage State**: Log critically, halt recording creation, and sleep-poll the disk until space is freed. Do not delete files.
- **Recoverable ALSA Failures**: `RecordingService` returns a failure. `SessionManager` logs the error, sleeps for `retry_backoff_sec`, and attempts to restart the stream.
- **Fatal Failures**: Unhandled exceptions bubble up, the application exits, and `systemd` handles the process restart.

## 8. Testing Strategy
- Heavy use of dependency injection for `RecordingService`, `StorageMonitor`, sleep/timing, and shutdown events to avoid real-time waiting.
- Mock disk states (e.g., full disk) to verify recording denial and sleep-polling behavior.
- Simulate an ALSA crash to test the `retry_backoff_sec` loop.
- Trigger shutdown events to assert that `RecordingService` finalizes the active WAV properly.
- All tests must run without Raspberry Pi hardware, real ALSA hardware, Internet access, real NTP servers, or root privileges.

## 9. Documentation Changes
- Add `docs/lifecycle.md` outlining the recording state machine, segment lifecycle, failure/recovery state transitions, storage-full behavior, shutdown behavior, and systemd architecture.
- Update `README.md` and `docs/architecture.md` asserting that the device operates without internet, relies on local Intranet NTP, has no public internet NTP fallback, uses `RecordingService` as the canonical path, supports 16-bit PCM, retains partial recordings, and is purely AUDIO-ONLY.

## 10. Acceptance Criteria
- Continuous segmented recording functions properly using the defined duration.
- Clean segment transitions (unique filenames, valid WAVs, no overwrites).
- System internally recovers from temporary ALSA failures (`retry_backoff_sec`).
- System halts recording cleanly when disk space drops below threshold.
- System handles disk becoming full *during* recording, keeping the partial WAV valid.
- System resumes recording when disk space becomes available again.
- SIGTERM/SIGINT cleanly stops the active capture and finalizes the file.
- `systemd` service runs smoothly without root privileges, cleanly handling process-level restarts.
- No Internet requirement, NTP synchronization success requirement for startup, or camera/video functionality introduced.
- Preservation of all Milestone 1/2 behaviors.

## 11. Decisions/Clarifications
- No automatic deletion of recordings is implemented.
- VAD, AI/ML, SMB/FTP uploads, cloud services, and camera functionality are entirely out of scope for Milestone 3.
