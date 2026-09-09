# Deployment Workflow

RTLS+ Audio uses a Master Image cloning workflow rather than performing manual installations per-device.

## 1. Master Raspberry Pi Preparation
The initial deployment must occur on a single "Master" Pi to establish dependencies, driver layers, and configuration topologies.

### Workflow:
1. **OS Base**: Flash standard Debian 13 (Trixie) onto the Master SD.
2. **ReSpeaker Driver**: Install the `seeed-voicecard` driver per manufacturer specs. Ensure `arecord -l` exposes the hardware.
3. **Application Install**: Run the provided `scripts/install.sh`. This prepares the `rtlsaudio` daemon user, configures directory paths, and mounts the systemd service.
4. **Configuration Mapping**: Map the local Intranet NTP (`time.ntp.server`) and adjust `audio.mixer.pga_gain_db` (defaults to 25dB) inside `/etc/rtls-audio/config.yaml`.
5. **Testing**: Trigger `rtls-audio status` and `systemctl start rtls-audio` to monitor successful daemon binding and 10-minute WAV segmentation outputs.
6. **Cleanup**: Before generating the clone image, purge old test recordings:
   ```bash
   sudo rm -rf /var/lib/rtls-audio/*.wav
   sudo rm -rf /var/log/rtls-audio/*.log
   ```

## 2. Cloning the Image
Clone the SD card using `dd`, `rpi-imager`, or similar utilities.

## 3. Cloned Device Configuration
When booting a freshly cloned Pi, the operator only needs to modify the unique device parameters in `/etc/rtls-audio/config.yaml`:
- **Device Identifiers** (If utilized in future deployments)
- **Hostnames**
- **NTP overrides** (if regional intranets differ)

The systemd service, Python dependencies, and ALSA configurations are carried over natively and will boot autonomously on start.
