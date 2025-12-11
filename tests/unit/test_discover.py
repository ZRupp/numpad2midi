"""Tests for device discovery module."""

from io import StringIO
from unittest.mock import Mock, patch, MagicMock

import pytest

from numpad2midi.discover import (
    list_input_devices,
    find_device_interactive,
    verify_device,
)


class TestListInputDevices:
    """Tests for list_input_devices function."""

    @patch("numpad2midi.discover.evdev")
    def test_list_devices_basic(self, mock_evdev: Mock, capsys) -> None:
        """Test listing devices with basic output."""
        mock_device1 = Mock()
        mock_device1.name = "USB Keyboard"
        mock_device1.path = "/dev/input/event0"

        mock_device2 = Mock()
        mock_device2.name = "Numpad"
        mock_device2.path = "/dev/input/event1"

        mock_evdev.list_devices.return_value = ["/dev/input/event0", "/dev/input/event1"]
        mock_evdev.InputDevice.side_effect = [mock_device1, mock_device2]

        list_input_devices(verbose=False)

        captured = capsys.readouterr()
        assert "Found 2 input device(s)" in captured.out
        assert "USB Keyboard" in captured.out
        assert "/dev/input/event0" in captured.out
        assert "Numpad" in captured.out
        assert "/dev/input/event1" in captured.out

    @patch("numpad2midi.discover.evdev")
    def test_list_devices_verbose(self, mock_evdev: Mock, capsys) -> None:
        """Test listing devices with verbose output."""
        mock_device = Mock()
        mock_device.name = "Test Device"
        mock_device.path = "/dev/input/event0"
        mock_device.phys = "usb-0000:00:14.0-1/input0"
        mock_device.info.vendor = 0x046D
        mock_device.info.product = 0xC52B
        mock_device.capabilities.return_value = {}

        mock_evdev.list_devices.return_value = ["/dev/input/event0"]
        mock_evdev.InputDevice.return_value = mock_device

        list_input_devices(verbose=True)

        captured = capsys.readouterr()
        assert "Test Device" in captured.out
        assert "Physical" in captured.out
        assert "Vendor" in captured.out
        assert "Product" in captured.out

    @patch("numpad2midi.discover.evdev")
    def test_list_devices_with_key_capabilities(self, mock_evdev: Mock, capsys) -> None:
        """Test listing devices with key event capabilities."""
        mock_device = Mock()
        mock_device.name = "Test Device"
        mock_device.path = "/dev/input/event0"
        mock_device.phys = "usb-test"
        mock_device.info.vendor = 0x0000
        mock_device.info.product = 0x0000

        # Simulate device with key events
        mock_evdev.ecodes.EV_KEY = 1
        mock_device.capabilities.return_value = {1: [1, 2, 3, 4, 5]}

        mock_evdev.list_devices.return_value = ["/dev/input/event0"]
        mock_evdev.InputDevice.return_value = mock_device

        list_input_devices(verbose=True)

        captured = capsys.readouterr()
        assert "Keys: 5 key events supported" in captured.out

    @patch("numpad2midi.discover.evdev")
    def test_list_devices_empty(self, mock_evdev: Mock, capsys) -> None:
        """Test listing devices when none available."""
        mock_evdev.list_devices.return_value = []

        list_input_devices(verbose=False)

        captured = capsys.readouterr()
        assert "No input devices found" in captured.out

    @patch("numpad2midi.discover.evdev")
    def test_list_devices_shows_usage_examples(self, mock_evdev: Mock, capsys) -> None:
        """Test that usage examples are shown."""
        mock_device = Mock()
        mock_device.name = "Test"
        mock_device.path = "/dev/input/event0"

        mock_evdev.list_devices.return_value = ["/dev/input/event0"]
        mock_evdev.InputDevice.return_value = mock_device

        list_input_devices(verbose=False)

        captured = capsys.readouterr()
        assert "To use a device" in captured.out
        assert "device:" in captured.out
        assert "name:" in captured.out
        assert "path:" in captured.out


class TestFindDeviceInteractive:
    """Tests for find_device_interactive function."""

    @patch("numpad2midi.discover.evdev")
    @patch("builtins.input")
    def test_select_first_device(self, mock_input: Mock, mock_evdev: Mock) -> None:
        """Test selecting first device."""
        mock_device1 = Mock()
        mock_device1.name = "Device 1"
        mock_device1.path = "/dev/input/event0"

        mock_device2 = Mock()
        mock_device2.name = "Device 2"
        mock_device2.path = "/dev/input/event1"

        mock_evdev.list_devices.return_value = ["/dev/input/event0", "/dev/input/event1"]
        mock_evdev.InputDevice.side_effect = [mock_device1, mock_device2]

        mock_input.return_value = "1"

        result = find_device_interactive()

        assert result == "/dev/input/event0"

    @patch("numpad2midi.discover.evdev")
    @patch("builtins.input")
    def test_select_second_device(self, mock_input: Mock, mock_evdev: Mock) -> None:
        """Test selecting second device."""
        mock_device1 = Mock()
        mock_device1.name = "Device 1"
        mock_device1.path = "/dev/input/event0"

        mock_device2 = Mock()
        mock_device2.name = "Device 2"
        mock_device2.path = "/dev/input/event1"

        mock_evdev.list_devices.return_value = ["/dev/input/event0", "/dev/input/event1"]
        mock_evdev.InputDevice.side_effect = [mock_device1, mock_device2]

        mock_input.return_value = "2"

        result = find_device_interactive()

        assert result == "/dev/input/event1"

    @patch("numpad2midi.discover.evdev")
    @patch("builtins.input")
    def test_cancel_selection(self, mock_input: Mock, mock_evdev: Mock) -> None:
        """Test cancelling device selection."""
        mock_device = Mock()
        mock_device.name = "Device"
        mock_device.path = "/dev/input/event0"

        mock_evdev.list_devices.return_value = ["/dev/input/event0"]
        mock_evdev.InputDevice.return_value = mock_device

        mock_input.return_value = "2"  # Cancel option for 1 device

        result = find_device_interactive()

        assert result is None

    @patch("numpad2midi.discover.evdev")
    @patch("builtins.input")
    def test_invalid_then_valid_selection(
        self, mock_input: Mock, mock_evdev: Mock
    ) -> None:
        """Test invalid selection followed by valid one."""
        mock_device = Mock()
        mock_device.name = "Device"
        mock_device.path = "/dev/input/event0"

        mock_evdev.list_devices.return_value = ["/dev/input/event0"]
        mock_evdev.InputDevice.return_value = mock_device

        mock_input.side_effect = ["99", "1"]

        result = find_device_interactive()

        assert result == "/dev/input/event0"
        assert mock_input.call_count == 2

    @patch("numpad2midi.discover.evdev")
    @patch("builtins.input")
    def test_non_numeric_input_then_cancel(
        self, mock_input: Mock, mock_evdev: Mock, capsys
    ) -> None:
        """Test handling non-numeric input followed by cancel."""
        mock_device = Mock()
        mock_device.name = "Device"
        mock_device.path = "/dev/input/event0"

        mock_evdev.list_devices.return_value = ["/dev/input/event0"]
        mock_evdev.InputDevice.return_value = mock_device

        # When ValueError is raised, it exits the loop in the except block
        mock_input.side_effect = ValueError("invalid literal")

        result = find_device_interactive()

        assert result is None
        captured = capsys.readouterr()
        assert "Cancelled" in captured.out

    @patch("numpad2midi.discover.evdev")
    @patch("builtins.input")
    def test_keyboard_interrupt(self, mock_input: Mock, mock_evdev: Mock) -> None:
        """Test handling keyboard interrupt."""
        mock_device = Mock()
        mock_device.name = "Device"
        mock_device.path = "/dev/input/event0"

        mock_evdev.list_devices.return_value = ["/dev/input/event0"]
        mock_evdev.InputDevice.return_value = mock_device

        mock_input.side_effect = KeyboardInterrupt()

        result = find_device_interactive()

        assert result is None

    @patch("numpad2midi.discover.evdev")
    def test_no_devices_available(self, mock_evdev: Mock) -> None:
        """Test when no devices available."""
        mock_evdev.list_devices.return_value = []

        result = find_device_interactive()

        assert result is None


class TestVerifyDeviceFunction:
    """Tests for verify_device function."""

    @patch("numpad2midi.discover.evdev")
    def test_device_permission_error(self, mock_evdev: Mock, capsys) -> None:
        """Test handling permission denied error."""
        mock_evdev.InputDevice.side_effect = PermissionError()

        verify_device("/dev/input/event0", timeout=5)

        captured = capsys.readouterr()
        assert "Permission denied" in captured.out
        assert "input" in captured.out

    @patch("numpad2midi.discover.evdev")
    def test_device_not_found(self, mock_evdev: Mock, capsys) -> None:
        """Test handling device not found error."""
        mock_evdev.InputDevice.side_effect = FileNotFoundError()

        verify_device("/dev/input/event0", timeout=5)

        captured = capsys.readouterr()
        assert "Device not found" in captured.out

    @patch("numpad2midi.discover.evdev")
    def test_generic_error(self, mock_evdev: Mock, capsys) -> None:
        """Test handling generic errors."""
        mock_evdev.InputDevice.side_effect = Exception("Something went wrong")

        verify_device("/dev/input/event0", timeout=5)

        captured = capsys.readouterr()
        assert "Error testing device" in captured.out
