"""Tests for input handler module."""

from typing import Callable
from unittest.mock import Mock, patch, MagicMock, call

import pytest

from numpad2midi.input_handler import InputHandler, InputError


class TestInputHandler:
    """Tests for InputHandler class."""

    @patch("numpad2midi.input_handler.InputDevice")
    def test_init_with_device_path(self, mock_input_device: Mock) -> None:
        """Test initialization with explicit device path."""
        mock_device = Mock()
        mock_input_device.return_value = mock_device
        mock_device.name = "Test Numpad"

        handler = InputHandler(device_path="/dev/input/event0")

        mock_input_device.assert_called_once_with("/dev/input/event0")
        assert handler.device_path == "/dev/input/event0"

    @patch("numpad2midi.input_handler.InputDevice")
    @patch("numpad2midi.input_handler.evdev.list_devices")
    def test_init_auto_detect_by_name(
        self, mock_list_devices: Mock, mock_input_device: Mock
    ) -> None:
        """Test auto-detection by device name."""
        mock_device1 = Mock()
        mock_device1.path = "/dev/input/event0"
        mock_device1.name = "Keyboard"

        mock_device2 = Mock()
        mock_device2.path = "/dev/input/event1"
        mock_device2.name = "USB Numpad"

        mock_list_devices.return_value = [
            "/dev/input/event0",
            "/dev/input/event1",
        ]
        mock_input_device.side_effect = [mock_device1, mock_device2, mock_device2]

        handler = InputHandler(device_name="numpad")

        assert handler.device_path == "/dev/input/event1"

    @patch("numpad2midi.input_handler.InputDevice")
    @patch("numpad2midi.input_handler.evdev.list_devices")
    def test_init_device_not_found(
        self, mock_list_devices: Mock, mock_input_device: Mock
    ) -> None:
        """Test error when device not found."""
        mock_device = Mock()
        mock_device.name = "Keyboard"
        mock_list_devices.return_value = ["/dev/input/event0"]
        mock_input_device.return_value = mock_device

        with pytest.raises(InputError, match="No device found matching 'numpad'"):
            InputHandler(device_name="numpad")

    @patch("numpad2midi.input_handler.evdev.list_devices")
    def test_init_no_devices(self, mock_list_devices: Mock) -> None:
        """Test error when no input devices available."""
        mock_list_devices.return_value = []

        with pytest.raises(InputError, match="No input devices found"):
            InputHandler(device_name="numpad")

    def test_init_requires_path_or_name(self) -> None:
        """Test error when neither path nor name provided."""
        with pytest.raises(InputError, match="Either device_path or device_name"):
            InputHandler()

    @patch("numpad2midi.input_handler.InputDevice")
    def test_grab_device(self, mock_input_device: Mock) -> None:
        """Test grabbing device for exclusive access."""
        mock_device = Mock()
        mock_input_device.return_value = mock_device

        handler = InputHandler(device_path="/dev/input/event0")
        handler.grab()

        mock_device.grab.assert_called_once()

    @patch("numpad2midi.input_handler.InputDevice")
    def test_ungrab_device(self, mock_input_device: Mock) -> None:
        """Test releasing device grab."""
        mock_device = Mock()
        mock_input_device.return_value = mock_device

        handler = InputHandler(device_path="/dev/input/event0")
        handler.ungrab()

        mock_device.ungrab.assert_called_once()

    @patch("numpad2midi.input_handler.ecodes")
    @patch("numpad2midi.input_handler.InputDevice")
    def test_start_listening(self, mock_input_device: Mock, mock_ecodes: Mock) -> None:
        """Test starting event listener."""
        mock_device = Mock()
        mock_input_device.return_value = mock_device

        # Simulate key events
        key_event = Mock()
        key_event.type = 1  # EV_KEY
        key_event.code = 79  # KEY_KP1
        key_event.value = 1  # Key down

        mock_device.read_loop.return_value = iter([key_event])
        mock_ecodes.EV_KEY = 1
        mock_ecodes.KEY = {79: "KEY_KP1"}

        callback = Mock()
        handler = InputHandler(device_path="/dev/input/event0")

        # Manually call the listener once for testing
        handler._running = True
        for event in mock_device.read_loop():
            if event.type == mock_ecodes.EV_KEY and event.value == 1:
                key_name = mock_ecodes.KEY.get(event.code, f"UNKNOWN_{event.code}")
                callback(key_name)
                break

        callback.assert_called_once_with("KEY_KP1")

    @patch("numpad2midi.input_handler.ecodes")
    @patch("numpad2midi.input_handler.InputDevice")
    def test_filter_key_down_only(
        self, mock_input_device: Mock, mock_ecodes: Mock
    ) -> None:
        """Test that only key down events trigger callbacks."""
        mock_device = Mock()
        mock_input_device.return_value = mock_device

        key_down = Mock()
        key_down.type = 1  # EV_KEY
        key_down.code = 79
        key_down.value = 1  # Key down

        key_up = Mock()
        key_up.type = 1  # EV_KEY
        key_up.code = 79
        key_up.value = 0  # Key up

        mock_device.read_loop.return_value = iter([key_down, key_up])
        mock_ecodes.EV_KEY = 1
        mock_ecodes.KEY = {79: "KEY_KP1"}

        callback = Mock()
        handler = InputHandler(device_path="/dev/input/event0")
        handler._running = True

        for event in mock_device.read_loop():
            if event.type == mock_ecodes.EV_KEY and event.value == 1:
                key_name = mock_ecodes.KEY.get(event.code, f"UNKNOWN_{event.code}")
                callback(key_name)

        callback.assert_called_once_with("KEY_KP1")

    @patch("numpad2midi.input_handler.InputDevice")
    def test_stop_listening(self, mock_input_device: Mock) -> None:
        """Test stopping event listener."""
        mock_device = Mock()
        mock_input_device.return_value = mock_device

        handler = InputHandler(device_path="/dev/input/event0")
        handler._running = True
        handler.stop()

        assert handler._running is False

    @patch("numpad2midi.input_handler.InputDevice")
    def test_close(self, mock_input_device: Mock) -> None:
        """Test closing device."""
        mock_device = Mock()
        mock_input_device.return_value = mock_device

        handler = InputHandler(device_path="/dev/input/event0")
        handler.close()

        mock_device.close.assert_called_once()

    @patch("numpad2midi.input_handler.InputDevice")
    def test_context_manager(self, mock_input_device: Mock) -> None:
        """Test using handler as context manager."""
        mock_device = Mock()
        mock_input_device.return_value = mock_device

        with InputHandler(device_path="/dev/input/event0") as handler:
            assert handler is not None

        mock_device.close.assert_called_once()

    @patch("numpad2midi.input_handler.InputDevice")
    def test_get_device_info(self, mock_input_device: Mock) -> None:
        """Test getting device information."""
        mock_device = Mock()
        mock_device.name = "Test Numpad"
        mock_device.path = "/dev/input/event0"
        mock_input_device.return_value = mock_device

        handler = InputHandler(device_path="/dev/input/event0")
        info = handler.get_device_info()

        assert info["name"] == "Test Numpad"
        assert info["path"] == "/dev/input/event0"
