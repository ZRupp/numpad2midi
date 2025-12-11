#!/bin/bash
# Uninstallation script for numpad2midi

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

info "Uninstalling numpad2midi..."

# Stop and disable all service instances
info "Stopping and disabling services..."
for service in /etc/systemd/system/multi-user.target.wants/numpad2midi@*.service; do
    if [ -e "$service" ]; then
        instance=$(basename "$service" | sed 's/numpad2midi@\(.*\)\.service/\1/')
        systemctl stop "numpad2midi@$instance.service" 2>/dev/null || true
        systemctl disable "numpad2midi@$instance.service" 2>/dev/null || true
    fi
done

# Remove systemd service
if [ -f "/etc/systemd/system/numpad2midi@.service" ]; then
    info "Removing systemd service..."
    rm /etc/systemd/system/numpad2midi@.service
    systemctl daemon-reload
fi

# Remove configuration (ask first)
if [ -d "/etc/numpad2midi" ]; then
    read -p "Remove configuration directory /etc/numpad2midi? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "Removing configuration..."
        rm -rf /etc/numpad2midi
    else
        warn "Keeping configuration directory"
    fi
fi

# Uninstall Python package
info "Uninstalling Python package..."
pip3 uninstall -y numpad2midi 2>/dev/null || warn "Package not found in pip"

info "Uninstallation complete!"
