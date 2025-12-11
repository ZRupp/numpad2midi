"""Device discovery utility for finding input devices."""

import logging
import select
from typing import Optional

import evdev

logger = logging.getLogger(__name__)


def list_input_devices(verbose: bool = False) -> None:
    """
    List all available input devices.

    Args:
        verbose: If True, show detailed device information
    """
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]

    if not devices:
        print("No input devices found on system.")
        return

    print(f"\nFound {len(devices)} input device(s):\n")
    print("-" * 80)

    for i, device in enumerate(devices, 1):
        print(f"{i}. {device.name}")
        print(f"   Path: {device.path}")

        if verbose:
            print(f"   Physical: {device.phys}")
            print(f"   Vendor: {device.info.vendor:#06x}")
            print(f"   Product: {device.info.product:#06x}")

            # Check if device has key events
            try:
                capabilities = device.capabilities()
                if evdev.ecodes.EV_KEY in capabilities:
                    key_count = len(capabilities[evdev.ecodes.EV_KEY])
                    print(f"   Keys: {key_count} key events supported")
            except Exception:
                pass

        print("-" * 80)

    print("\nTo use a device, add to your config.yaml:")
    print("\nOption 1 - By name pattern (partial match, case-insensitive):")
    print("  device:")
    print('    name: "USB"  # Matches any device with "USB" in name')
    print("\nOption 2 - By exact path:")
    print("  device:")
    print(f'    path: "{devices[0].path}"')
    print("\nOption 3 - By stable ID (recommended, survives reboots):")
    print("  Run: ls -l /dev/input/by-id/")
    print("  Then use the stable path in your config")


def find_device_interactive() -> Optional[str]:
    """
    Interactive device selection.

    Returns:
        Selected device path or None if cancelled
    """
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]

    if not devices:
        print("No input devices found on system.")
        return None

    print("\nAvailable input devices:\n")
    for i, device in enumerate(devices, 1):
        print(f"{i}. {device.name}")
        print(f"   {device.path}")

    print(f"\n{len(devices) + 1}. Cancel")

    while True:
        try:
            choice = input(f"\nSelect device (1-{len(devices) + 1}): ").strip()
            idx = int(choice) - 1

            if idx == len(devices):
                return None

            if 0 <= idx < len(devices):
                selected = devices[idx]
                print(f"\nSelected: {selected.name}")
                print(f"Path: {selected.path}")
                return selected.path

            print(f"Invalid choice. Please enter 1-{len(devices) + 1}")

        except (ValueError, KeyboardInterrupt):
            print("\nCancelled.")
            return None


def verify_device(device_path: str, timeout: int = 5) -> None:
    """
    Verify an input device by showing key presses.

    Args:
        device_path: Path to input device
        timeout: How long to listen for events (seconds)
    """
    try:
        device = evdev.InputDevice(device_path)
        print(f"\nTesting device: {device.name}")
        print(f"Path: {device.path}")
        print(f"\nPress keys on your device (listening for {timeout} seconds)...")
        print("Press Ctrl+C to stop early.\n")

        event_count = 0
        start_time = evdev.util.timestamp()

        while True:
            # Check timeout
            if evdev.util.timestamp() - start_time > timeout:
                break

            # Wait for events with timeout
            r, w, x = select.select([device.fd], [], [], 0.1)
            if not r:
                continue

            for event in device.read():
                if event.type == evdev.ecodes.EV_KEY:
                    key_event = evdev.categorize(event)
                    if event.value == 1:  # Key down
                        key_name = evdev.ecodes.KEY.get(
                            event.code, f"UNKNOWN_{event.code}"
                        )
                        print(f"  ✓ Key pressed: {key_name} (code: {event.code})")
                        event_count += 1

        if event_count == 0:
            print("\nNo key events detected.")
            print("This device may not be a keyboard/numpad, or no keys were pressed.")
        else:
            print(f"\n✓ Device is working! Detected {event_count} key press(es).")
            print(f"\nUse this in your config.yaml:")
            print(f"  device:")
            print(f'    path: "{device_path}"')

    except PermissionError:
        print(f"\nPermission denied accessing {device_path}")
        print("Try running with sudo, or add your user to the 'input' group:")
        print("  sudo usermod -a -G input $USER")
        print("  (then log out and back in)")
    except FileNotFoundError:
        print(f"\nDevice not found: {device_path}")
    except KeyboardInterrupt:
        print("\n\nStopped by user.")
    except Exception as e:
        print(f"\nError testing device: {e}")
