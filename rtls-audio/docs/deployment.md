# Deployment Workflow

RTLS+ Audio uses a Master Image cloning workflow rather than performing manual installations per-device. The application is strictly **AUDIO-ONLY** and is designed to operate securely on an **isolated Intranet** using a Windows SMB File Server for permanent storage.

## 1. Master Raspberry Pi Preparation
The initial deployment must occur on a single "Master" Pi to establish dependencies, driver layers, and configuration topologies.

### Workflow:
1. **OS Base**: Flash standard Debian 13 (Trixie) onto the Master SD.
2. **ReSpeaker Driver**: Install the `seeed-voicecard` driver per manufacturer specs. Ensure `arecord -l` exposes the hardware.
3. **SMB Configuration**: The application does **not** manage its own SMB hooks. Mount the Windows Intranet File Server natively via `/etc/fstab`.
   * Create credentials securely (`chmod 600`): `/etc/rtls-audio/smb-credentials`
   * Map the `fstab` CIFS definition specifying `/mnt/recordings` ensuring the `rtlsaudio` user has `rw` access natively.
4. **Application Install**: Run the provided `scripts/install.sh`. This prepares the `rtlsaudio` daemon user, configures directory paths, and prepares the systemd daemon.
5. **Configuration Mapping**: Open `/etc/rtls-audio/config.yaml`:
   * Map local Intranet NTP (`time.ntp.server`). **No public pools are permitted.**
   * Configure PGA Gain `audio.mixer.pga_gain_db` (defaults to 25dB).
   * Specify `storage.recording_path` to map the SMB target (`/mnt/recordings`), and set `smb.enabled: true`.
6. **Testing**: Trigger `rtls-audio status` asserting that ALSA, SMB Mounts, Storage Space, and Hardware constraints are successfully bound.
7. **Cleanup**: Before generating the clone image, safely purge old test recordings:
   ```bash
   sudo rm -rf /mnt/recordings/*.wav
   sudo rm -rf /var/log/rtls-audio/*.log
   ```

## 2. Cloning the Image
Clone the SD card using `dd`, `rpi-imager`, or similar utilities.

## 3. Cloned Device Configuration
When booting a freshly cloned Pi, the operator modifies only the unique device parameters in `/etc/rtls-audio/config.yaml` or network rules:
- **SMB Server/Share Configurations** (If targeting a different sector file-server)
- **SMB Credentials** (Update `/etc/rtls-audio/smb-credentials` safely)
- **Hostnames / Device Allocations**
- **NTP overrides** (if regional intranets differ)

The systemd service (`rtls-audio.service`) utilizes `RequiresMountsFor=/mnt/recordings` and will seamlessly orchestrate startup sequences relying safely on the local `/etc/fstab` OS-layer.
