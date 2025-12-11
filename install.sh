#!/bin/bash
# Installation script for numpad2midi

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root (use sudo)"
    exit 1
fi

# Detect the user who invoked sudo
if [ -n "$SUDO_USER" ]; then
    REAL_USER="$SUDO_USER"
else
    error "Could not detect user. Please run with sudo."
    exit 1
fi

info "Installing numpad2midi for user: $REAL_USER"

# Install Python package
info "Installing Python package..."
pip3 install -e .

# Create config directory
info "Creating configuration directory..."
mkdir -p /etc/numpad2midi
cp config/default.yaml /etc/numpad2midi/config.yaml
chmod 644 /etc/numpad2midi/config.yaml

# Add user to input group if not already a member
if ! id -nG "$REAL_USER" | grep -qw "input"; then
    info "Adding $REAL_USER to 'input' group..."
    usermod -a -G input "$REAL_USER"
    warn "User added to 'input' group. You may need to log out and back in for changes to take effect."
else
    info "User $REAL_USER is already in 'input' group"
fi

# Install systemd service
info "Installing systemd service..."
cp systemd/numpad2midi.service /etc/systemd/system/numpad2midi@.service
systemctl daemon-reload

info "Installation complete!"
echo ""
info "Next steps:"
echo "  1. Edit configuration: /etc/numpad2midi/config.yaml"
echo "  2. Enable service: sudo systemctl enable numpad2midi@$REAL_USER.service"
echo "  3. Start service: sudo systemctl start numpad2midi@$REAL_USER.service"
echo "  4. Check status: sudo systemctl status numpad2midi@$REAL_USER.service"
echo "  5. View logs: sudo journalctl -u numpad2midi@$REAL_USER.service -f"
echo ""
warn "If you were just added to the 'input' group, you may need to log out and back in."
