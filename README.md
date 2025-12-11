# numpad2midi

[![Tests](https://img.shields.io/badge/tests-72%20passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-83%25-brightgreen)](htmlcov/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

A background service for Linux that converts numpad key presses into MIDI messages, designed for controlling [MODEP](https://blokas.io/modep/) (MOD Emulator for Raspberry Pi) with a simple USB numpad.

## Features

- **Flexible Input**: Auto-detect numpad devices by name or use explicit device paths
- **Multiple MIDI Actions**: Support for Program Change, Control Change, Note On/Off
- **Virtual MIDI Ports**: Create virtual MIDI ports or connect to physical ones
- **Systemd Integration**: Run as a background service with auto-restart
- **Test-Driven**: 72 tests with 83% code coverage
- **Well-Documented**: Clear configuration with examples for MODEP
- **Type-Safe**: Full type hints and validation using Pydantic

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ZRupp/numpad2midi.git
cd numpad2midi

# Run installation script
sudo ./install.sh
```

### Find Your Device

**Important**: Most USB numpads don't have "numpad" in their device name! Before configuring, find your device:

```bash
# List all input devices
numpad2midi list-devices

# Test your device (interactive selection)
numpad2midi test-device

# Test specific device
numpad2midi test-device /dev/input/event0
```

### Configuration

Edit `/etc/numpad2midi/config.yaml` with your device name:

```yaml
device:
  name: "numpad"  # Auto-detect device with "numpad" in name

midi:
  port_name: "numpad2midi"
  virtual_port: true

mappings:
  - key: "KEY_KP0"
    action:
      type: "program_change"
      channel: 0
      program: 0
```

### Running as a Service

```bash
# Enable and start the service
sudo systemctl enable numpad2midi@$USER.service
sudo systemctl start numpad2midi@$USER.service

# Check status
sudo systemctl status numpad2midi@$USER.service

# View logs
sudo journalctl -u numpad2midi@$USER.service -f
```

### Manual Usage

```bash
# List available input devices
numpad2midi list-devices

# Test a device interactively
numpad2midi test-device

# Run with default config
numpad2midi run config/default.yaml

# Run with verbose logging
numpad2midi run --verbose config/default.yaml

# Run with device grab (exclusive access)
numpad2midi run --grab config/default.yaml

# Backwards compatible (no "run" needed)
numpad2midi config/default.yaml
```

## Configuration

### Device Configuration

```yaml
device:
  # Option 1: Auto-detect by name pattern (case-insensitive)
  name: "numpad"

  # Option 2: Explicit device path
  path: "/dev/input/event0"

  # Option 3: Use device ID (more stable across reboots)
  path: "/dev/input/by-id/usb-Your_Numpad-event-kbd"
```

### MIDI Configuration

```yaml
midi:
  port_name: "numpad2midi"  # Name of MIDI port
  virtual_port: true         # Create virtual port (true) or connect to existing (false)
```

### Key Mappings

#### Program Change
```yaml
- key: "KEY_KP0"
  action:
    type: "program_change"
    channel: 0      # MIDI channel (0-15)
    program: 0      # Program number (0-127)
```

#### Control Change
```yaml
- key: "KEY_NUMLOCK"
  action:
    type: "control_change"
    channel: 0      # MIDI channel (0-15)
    controller: 64  # CC number (0-127)
    value: 127      # CC value (0-127)
```

#### Note On/Off
```yaml
- key: "KEY_KPDOT"
  action:
    type: "note_on"
    channel: 0      # MIDI channel (0-15)
    note: 60        # MIDI note (0-127, Middle C = 60)
    velocity: 100   # Note velocity (0-127)
```

### Finding Key Names

The easiest way to find key names:

```bash
# Test your device and see key names as you press them
numpad2midi test-device
```

Alternative using evtest:

```bash
# Install evtest
sudo apt-get install evtest

# Run evtest and select your numpad
sudo evtest

# Press keys to see their event codes (e.g., KEY_KP0, KEY_NUMLOCK)
```

## MODEP Integration

### Example: Basic Preset Switching

```yaml
mappings:
  # Numpad 0-9: Select presets 0-9
  - key: "KEY_KP0"
    action: {type: "program_change", channel: 0, program: 0}
  - key: "KEY_KP1"
    action: {type: "program_change", channel: 0, program: 1}
  # ... continue for KEY_KP2 through KEY_KP9

  # NumLock: Bypass toggle
  - key: "KEY_NUMLOCK"
    action: {type: "control_change", channel: 0, controller: 64, value: 127}
```

### Example: Advanced Control

```yaml
mappings:
  # Presets
  - key: "KEY_KP1"
    action: {type: "program_change", channel: 0, program: 0}

  # Effect bypass
  - key: "KEY_NUMLOCK"
    action: {type: "control_change", channel: 0, controller: 64, value: 127}

  # Volume control
  - key: "KEY_KPPLUS"
    action: {type: "control_change", channel: 0, controller: 7, value: 127}
  - key: "KEY_KPMINUS"
    action: {type: "control_change", channel: 0, controller: 7, value: 100}

  # Tap tempo
  - key: "KEY_KPDOT"
    action: {type: "note_on", channel: 0, note: 60, velocity: 100}
```

## Troubleshooting

### Service won't start

Check logs:
```bash
sudo journalctl -u numpad2midi@$USER.service -n 50
```

Common issues:
- **Device not found**: Run `ls -l /dev/input/by-id/` to find your numpad device
- **Permission denied**: Ensure user is in `input` group: `groups $USER`
- **MIDI port error**: Check if ALSA/JACK is running

### Device not detected

**This is the most common issue!** Many numpads don't have "numpad" in their name.

```bash
# List all input devices with their names
numpad2midi list-devices

# Find your device - look for USB devices or your numpad brand
# Common names: "USB Keyboard", "Numeric Keypad", "1.3", etc.

# Test to confirm it's the right device
numpad2midi test-device

# Update your config with the correct name pattern
# Example: if device is "USB Keyboard", use:
device:
  name: "USB"  # Partial match works!
```

Alternative methods:

```bash
# List all input devices by ID (more stable)
ls -l /dev/input/by-id/

# Test device access directly
sudo evtest /dev/input/eventX
```

### MIDI not working

```bash
# List MIDI ports
aconnect -l  # For ALSA
jack_lsp     # For JACK

# Test MIDI output
aseqdump -p "numpad2midi"
```

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for:
- Development setup
- Running tests
- Code architecture
- Contributing guidelines

## Requirements

- Python 3.9 or higher
- Linux with evdev support
- ALSA or JACK MIDI system
- Input device (numpad recommended)

### Python Dependencies

- `evdev>=1.6.0` - Linux input device interface
- `python-rtmidi>=1.5.0` - MIDI I/O
- `PyYAML>=6.0` - Configuration parsing
- `pydantic>=2.0.0` - Configuration validation

## Raspberry Pi Setup

For Raspberry Pi with MODEP:

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install python3-pip python3-dev libasound2-dev

# Clone and install
git clone https://github.com/ZRupp/numpad2midi.git
cd numpad2midi
sudo ./install.sh

# Configure for your numpad
sudo nano /etc/numpad2midi/config.yaml

# Enable service
sudo systemctl enable numpad2midi@pi.service
sudo systemctl start numpad2midi@pi.service

# Reboot (to apply group membership)
sudo reboot
```

## Uninstallation

```bash
sudo ./uninstall.sh
```

This will:
- Stop and disable the service
- Remove systemd service file
- Ask before removing configuration
- Uninstall Python package

## License

MIT License - see [LICENSE](LICENSE) for details

## Contributing

Contributions welcome! Please see [DEVELOPMENT.md](DEVELOPMENT.md) for guidelines.

## Acknowledgments

- Built for [MODEP](https://blokas.io/modep/) by Blokas
- Inspired by the need for simple, tactile control of guitar effects
- Thanks to the Python evdev and rtmidi communities

## Support

- **Issues**: [GitHub Issues](https://github.com/ZRupp/numpad2midi/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ZRupp/numpad2midi/discussions)

---

Made with ❤️ for musicians who prefer hardware controls over touchscreens
