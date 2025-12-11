"""Input device handler for capturing numpad events."""

import logging
import threading
from typing import Callable, Optional

import evdev
from evdev import InputDevice, categorize, ecodes

logger = logging.getLogger(__name__)


class InputError(Exception):
    """Input device related errors."""

    pass


class InputHandler:
    """
    Handles input device operations for capturing key presses.

    Supports auto-detection by device name or explicit device path.
    """

    def __init__(
        self,
        device_path: Optional[str] = None,
        device_name: Optional[str] = None,
    ) -> None:
        """
        Initialize input handler.

        Args:
            device_path: Explicit path to input device (e.g., /dev/input/event0)
            device_name: Pattern to match device name for auto-detection

        Raises:
            InputError: If device not found or initialization fails
        """
        if device_path is None and device_name is None:
            raise InputError("Either device_path or device_name must be provided")

        self.device_path: str
        self._device: Optional[InputDevice] = None
        self._running = False
        self._listener_thread: Optional[threading.Thread] = None

        try:
            if device_path:
                self.device_path = device_path
                self._device = InputDevice(device_path)
                logger.info(f"Opened input device: {self._device.name} at {device_path}")
            else:
                self.device_path = self._find_device(device_name or "")
                self._device = InputDevice(self.device_path)
                logger.info(
                    f"Auto-detected device: {self._device.name} at {self.device_path}"
                )

        except Exception as e:
            raise InputError(f"Failed to initialize input device: {e}")

    def _find_device(self, name_pattern: str) -> str:
        """
        Find input device by name pattern.

        Args:
            name_pattern: Pattern to match in device name (case-insensitive)

        Returns:
            Path to matching device

        Raises:
            InputError: If no matching device found
        """
        devices = [InputDevice(path) for path in evdev.list_devices()]

        if not devices:
            raise InputError("No input devices found on system")

        name_pattern_lower = name_pattern.lower()

        for device in devices:
            if name_pattern_lower in device.name.lower():
                return device.path

        available = ", ".join([f"{d.name} ({d.path})" for d in devices])
        raise InputError(
            f"No device found matching '{name_pattern}'. Available: {available}"
        )

    def grab(self) -> None:
        """Grab device for exclusive access."""
        if self._device:
            self._device.grab()
            logger.debug(f"Grabbed device: {self._device.name}")

    def ungrab(self) -> None:
        """Release device grab."""
        if self._device:
            self._device.ungrab()
            logger.debug(f"Ungrabbed device: {self._device.name}")

    def start_listening(self, callback: Callable[[str], None], grab: bool = False) -> None:
        """
        Start listening for key press events in a background thread.

        Args:
            callback: Function to call with key name when key is pressed
            grab: If True, grab device for exclusive access
        """
        if self._running:
            logger.warning("Listener already running")
            return

        if grab:
            self.grab()

        self._running = True
        self._listener_thread = threading.Thread(
            target=self._event_loop, args=(callback,), daemon=True
        )
        self._listener_thread.start()
        logger.info("Started input event listener")

    def _event_loop(self, callback: Callable[[str], None]) -> None:
        """
        Main event loop for processing input events.

        Args:
            callback: Function to call with key name
        """
        if self._device is None:
            logger.error("Device not initialized")
            return

        try:
            for event in self._device.read_loop():
                if not self._running:
                    break

                # Only process key events
                if event.type == ecodes.EV_KEY:
                    # Only trigger on key down (value 1), not key up (value 0)
                    if event.value == 1:
                        key_name = ecodes.KEY.get(event.code, f"UNKNOWN_{event.code}")
                        logger.debug(f"Key pressed: {key_name}")
                        try:
                            callback(key_name)
                        except Exception as e:
                            logger.error(f"Error in key callback: {e}")

        except OSError as e:
            if self._running:
                logger.error(f"Device read error: {e}")
                self._running = False
        except Exception as e:
            logger.error(f"Unexpected error in event loop: {e}")
            self._running = False

    def stop(self) -> None:
        """Stop listening for events."""
        if self._running:
            self._running = False
            if self._listener_thread:
                self._listener_thread.join(timeout=2.0)
            logger.info("Stopped input event listener")

    def close(self) -> None:
        """Close the input device."""
        self.stop()
        if self._device:
            try:
                self._device.close()
                logger.info(f"Closed input device: {self.device_path}")
            except Exception as e:
                logger.warning(f"Error closing input device: {e}")

    def get_device_info(self) -> dict[str, str]:
        """
        Get information about the input device.

        Returns:
            Dictionary with device name and path
        """
        return {
            "name": self._device.name if self._device else "Unknown",
            "path": self.device_path,
        }

    def __enter__(self) -> "InputHandler":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Context manager exit."""
        self.close()
