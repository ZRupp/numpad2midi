"""Tests for service orchestrator module."""

from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

import pytest

from numpad2midi.config import (
    Config,
    DeviceConfig,
    MidiConfig,
    KeyMapping,
    MidiAction,
    ActionType,
)
from numpad2midi.service import Service, ServiceError


class TestService:
    """Tests for Service class."""

    def _create_test_config(self) -> Config:
        """Helper to create a test configuration."""
        device = DeviceConfig(path="/dev/input/event0")
        midi = MidiConfig(port_name="test_port", virtual_port=True)
        action = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=0)
        mappings = [KeyMapping(key="KEY_KP0", action=action)]
        return Config(device=device, midi=midi, mappings=mappings)

    @patch("numpad2midi.service.Mapper")
    @patch("numpad2midi.service.MidiHandler")
    @patch("numpad2midi.service.InputHandler")
    def test_init_with_device_path(
        self, mock_input_handler: Mock, mock_midi_handler: Mock, mock_mapper: Mock
    ) -> None:
        """Test initialization with device path."""
        config = self._create_test_config()
        service = Service(config)

        mock_input_handler.assert_called_once_with(device_path="/dev/input/event0")
        mock_midi_handler.assert_called_once_with(port_name="test_port", virtual_port=True)
        mock_mapper.assert_called_once_with(config.mappings)

    @patch("numpad2midi.service.Mapper")
    @patch("numpad2midi.service.MidiHandler")
    @patch("numpad2midi.service.InputHandler")
    def test_init_with_device_name(
        self, mock_input_handler: Mock, mock_midi_handler: Mock, mock_mapper: Mock
    ) -> None:
        """Test initialization with device name."""
        device = DeviceConfig(name="numpad")
        midi = MidiConfig(port_name="test_port")
        action = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=0)
        mappings = [KeyMapping(key="KEY_KP0", action=action)]
        config = Config(device=device, midi=midi, mappings=mappings)

        service = Service(config)

        mock_input_handler.assert_called_once_with(device_name="numpad")

    @patch("numpad2midi.service.Mapper")
    @patch("numpad2midi.service.MidiHandler")
    @patch("numpad2midi.service.InputHandler")
    def test_start(
        self, mock_input_handler: Mock, mock_midi_handler: Mock, mock_mapper: Mock
    ) -> None:
        """Test starting the service."""
        config = self._create_test_config()
        mock_input_instance = Mock()
        mock_input_handler.return_value = mock_input_instance

        service = Service(config)
        service.start(grab_device=True)

        mock_input_instance.start_listening.assert_called_once()
        call_args = mock_input_instance.start_listening.call_args
        assert call_args[1]["grab"] is True

    @patch("numpad2midi.service.Mapper")
    @patch("numpad2midi.service.MidiHandler")
    @patch("numpad2midi.service.InputHandler")
    def test_stop(
        self, mock_input_handler: Mock, mock_midi_handler: Mock, mock_mapper: Mock
    ) -> None:
        """Test stopping the service."""
        config = self._create_test_config()
        mock_input_instance = Mock()
        mock_midi_instance = Mock()
        mock_input_handler.return_value = mock_input_instance
        mock_midi_handler.return_value = mock_midi_instance

        service = Service(config)
        service.stop()

        mock_input_instance.stop.assert_called_once()
        mock_input_instance.close.assert_called_once()
        mock_midi_instance.close.assert_called_once()

    @patch("numpad2midi.service.Mapper")
    @patch("numpad2midi.service.MidiHandler")
    @patch("numpad2midi.service.InputHandler")
    def test_key_callback_with_mapped_key(
        self, mock_input_handler: Mock, mock_midi_handler: Mock, mock_mapper: Mock
    ) -> None:
        """Test key callback with a mapped key."""
        config = self._create_test_config()
        mock_mapper_instance = Mock()
        mock_midi_instance = Mock()
        mock_mapper.return_value = mock_mapper_instance
        mock_midi_handler.return_value = mock_midi_instance

        action = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=5)
        mock_mapper_instance.get_action.return_value = action

        service = Service(config)
        service._on_key_press("KEY_KP0")

        mock_mapper_instance.get_action.assert_called_once_with("KEY_KP0")
        mock_midi_instance.send_action.assert_called_once_with(action)

    @patch("numpad2midi.service.Mapper")
    @patch("numpad2midi.service.MidiHandler")
    @patch("numpad2midi.service.InputHandler")
    def test_key_callback_with_unmapped_key(
        self, mock_input_handler: Mock, mock_midi_handler: Mock, mock_mapper: Mock
    ) -> None:
        """Test key callback with an unmapped key."""
        config = self._create_test_config()
        mock_mapper_instance = Mock()
        mock_midi_instance = Mock()
        mock_mapper.return_value = mock_mapper_instance
        mock_midi_handler.return_value = mock_midi_instance

        mock_mapper_instance.get_action.return_value = None

        service = Service(config)
        service._on_key_press("KEY_UNKNOWN")

        mock_mapper_instance.get_action.assert_called_once_with("KEY_UNKNOWN")
        mock_midi_instance.send_action.assert_not_called()

    @patch("numpad2midi.service.Mapper")
    @patch("numpad2midi.service.MidiHandler")
    @patch("numpad2midi.service.InputHandler")
    def test_key_callback_with_midi_error(
        self, mock_input_handler: Mock, mock_midi_handler: Mock, mock_mapper: Mock
    ) -> None:
        """Test key callback handles MIDI errors gracefully."""
        config = self._create_test_config()
        mock_mapper_instance = Mock()
        mock_midi_instance = Mock()
        mock_mapper.return_value = mock_mapper_instance
        mock_midi_handler.return_value = mock_midi_instance

        action = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=0)
        mock_mapper_instance.get_action.return_value = action
        mock_midi_instance.send_action.side_effect = Exception("MIDI error")

        service = Service(config)
        # Should not raise exception
        service._on_key_press("KEY_KP0")

        mock_midi_instance.send_action.assert_called_once()

    @patch("numpad2midi.service.Mapper")
    @patch("numpad2midi.service.MidiHandler")
    @patch("numpad2midi.service.InputHandler")
    def test_context_manager(
        self, mock_input_handler: Mock, mock_midi_handler: Mock, mock_mapper: Mock
    ) -> None:
        """Test using service as context manager."""
        config = self._create_test_config()
        mock_input_instance = Mock()
        mock_midi_instance = Mock()
        mock_input_handler.return_value = mock_input_instance
        mock_midi_handler.return_value = mock_midi_instance

        with Service(config) as service:
            assert service is not None

        mock_input_instance.stop.assert_called_once()
        mock_input_instance.close.assert_called_once()
        mock_midi_instance.close.assert_called_once()

    @patch("numpad2midi.service.Mapper")
    @patch("numpad2midi.service.MidiHandler")
    @patch("numpad2midi.service.InputHandler")
    def test_init_error_propagation(
        self, mock_input_handler: Mock, mock_midi_handler: Mock, mock_mapper: Mock
    ) -> None:
        """Test that initialization errors are propagated."""
        config = self._create_test_config()
        mock_input_handler.side_effect = Exception("Input init failed")

        with pytest.raises(ServiceError, match="Failed to initialize"):
            Service(config)
