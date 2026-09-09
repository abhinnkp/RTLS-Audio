#!/bin/bash
# Note: No set -e used to prevent bash session termination

echo "Starting RTLS+ Audio Production Setup..."

# 1. OS & Python Check
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed."
    # exit removed
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')

# 2. Dependencies
echo "Installing OS dependencies..."
apt-get update && apt-get install -y libasound2-dev

# 3. Create Service User
if ! id "rtlsaudio" &>/dev/null; then
    echo "Creating 'rtlsaudio' service account..."
    useradd -r -s /bin/false rtlsaudio
else
    echo "'rtlsaudio' user already exists."
fi

echo "Adding 'rtlsaudio' to 'audio' group..."
usermod -aG audio rtlsaudio

# 4. Provision Directories
echo "Provisioning directories..."
mkdir -p /etc/rtls-audio /var/lib/rtls-audio /var/log/rtls-audio
chown -R rtlsaudio:rtlsaudio /var/lib/rtls-audio /var/log/rtls-audio

# 5. Install Application
echo "Installing RTLS+ Audio Python package..."
pip install .

# 6. Configuration Backup & Provision
if [ -f /etc/rtls-audio/config.yaml ]; then
    echo "Backing up existing config.yaml..."
    cp /etc/rtls-audio/config.yaml /etc/rtls-audio/config.yaml.bak
fi

if [ -f config/config.yaml ]; then
    cp config/config.yaml /etc/rtls-audio/config.yaml
    chown rtlsaudio:rtlsaudio /etc/rtls-audio/config.yaml
fi

# 7. Install systemd service
echo "Installing systemd service..."
if [ -f systemd/rtls-audio.service ]; then
    cp systemd/rtls-audio.service /etc/systemd/system/
    systemctl daemon-reload
    echo "Service installed. You can enable it via: sudo systemctl enable --now rtls-audio"
fi

echo "RTLS+ Audio Production Setup Complete!"
