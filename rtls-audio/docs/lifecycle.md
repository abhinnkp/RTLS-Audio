# Recording Lifecycle and State Machine

## 1. Overview
RTLS+ Audio uses the `SessionManager` to orchestrate 24/7 autonomous audio captures without memory overflows, storage destruction, or manual intervention.

**Constraints**:
- The project is strictly **AUDIO-ONLY**.
- The device operates offline without Internet, relying on local configuration.

## 2. State Machine (`SessionManagerState`)
- `IDLE`: Startup state or waiting gracefully between clean segment completions.
- `RECORDING`: Actively pulling stream chunks from ALSA via the `RecordingService`.
- `STORAGE_BLOCKED`: Disk space constraints violated configured thresholds. `SessionManager` is polling storage availability before generating the next WAV file.
- `RETRY_WAIT`: A non-fatal ALSA crash (e.g. read error) occurred. Wait `recording.retry_backoff_sec` before attempting to re-lock the ALSA stream.
- `SHUTTING_DOWN`: Received `SIGTERM`/`SIGINT`. Immediate break out of `RECORDING` state gracefully trimming and closing the WAV file.

## 3. Storage and Retention Policy
- The daemon checks bounds **before** opening new segment files.
- If storage vanishes mid-segment, the current segment is safely truncated and stored, then the state transitions to `STORAGE_BLOCKED`.
- **Zero auto-deletion**: Milestone 3 explicitly refuses to delete or overwrite old recordings. New segments simply resume whenever an administrator or external process frees space.

## 4. Systemd Deployment (Non-Root)
Deploying via `/etc/systemd/system/rtls-audio.service` requires configuring `User=` to a dedicated account belonging to the `audio` group to interact with ALSA. It uses `Restart=always` alongside `ExecStart=/usr/local/bin/rtls-audio run` to recover from fatal OS drops outside of the local `RETRY_WAIT` ALSA backoffs.

## 5. Scope Limit Warnings
The `SessionManager` intentionally leaves out Voice Activity Detection (VAD) and automatic Network Uploading blocks. These functions remain architecturally isolated for future deployment paths.
