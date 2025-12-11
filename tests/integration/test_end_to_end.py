"""End-to-end integration tests."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from numpad2midi.config import load_config
from numpad2midi.service import Service


class TestEndToEnd:
    """End-to-end integration tests."""

    def _create_test_config_file(self) -> Path:
        """Create a temporary config file for testing."""
        config_data = {
            "device": {"path": "/dev/input/event0"},
            "midi": {"port_name": "test_midi", "virtual_port": True},
            "mappings": [
                {
                    "key": "KEY_KP0",
                    "action": {"type": "program_change", "channel": 0, "program": 0},
                },
                {
                    "key": "KEY_KP1",
                    "action": {"type": "program_change", "channel": 0, "program": 1},
                },
                {
                    "key": "KEY_NUMLOCK",
                    "action": {
                        "type": "control_change",
                        "channel": 0,
                        "controller": 64,
                        "value": 127,
                    },
                },
            ],
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(config_data, f)
            return Path(f.name)

    def test_load_config_and_create_service(self) -> None:
        """Test loading config and creating service."""
        config_file = self._create_test_config_file()

        try:
            config = load_config(config_file)
            assert config.device.path == "/dev/input/event0"
            assert config.midi.port_name == "test_midi"
            assert len(config.mappings) == 3
        finally:
            config_file.unlink()

    @patch("numpad2midi.service.Mapper")
    @patch("numpad2midi.service.MidiHandler")
    @patch("numpad2midi.service.InputHandler")
    def test_full_service_lifecycle(
        self, mock_input_handler: Mock, mock_midi_handler: Mock, mock_mapper: Mock
    ) -> None:
        """Test complete service lifecycle from config to shutdown."""
        config_file = self._create_test_config_file()

        try:
            # Load config
            config = load_config(config_file)

            # Create service
            mock_input_instance = Mock()
            mock_midi_instance = Mock()
            mock_mapper_instance = Mock()

            mock_input_handler.return_value = mock_input_instance
            mock_midi_handler.return_value = mock_midi_instance
            mock_mapper.return_value = mock_mapper_instance

            service = Service(config)

            # Start service
            service.start(grab_device=False)
            mock_input_instance.start_listening.assert_called_once()

            # Stop service
            service.stop()
            mock_input_instance.stop.assert_called_once()
            mock_input_instance.close.assert_called_once()
            mock_midi_instance.close.assert_called_once()

        finally:
            config_file.unlink()

    @patch("numpad2midi.service.Mapper")
    @patch("numpad2midi.service.MidiHandler")
    @patch("numpad2midi.service.InputHandler")
    def test_key_press_to_midi_flow(
        self, mock_input_handler: Mock, mock_midi_handler: Mock, mock_mapper: Mock
    ) -> None:
        """Test complete flow from key press to MIDI output."""
        config_file = self._create_test_config_file()

        try:
            config = load_config(config_file)

            mock_input_instance = Mock()
            mock_midi_instance = Mock()
            mock_mapper_instance = Mock()

            mock_input_handler.return_value = mock_input_instance
            mock_midi_handler.return_value = mock_midi_instance
            mock_mapper.return_value = mock_mapper_instance

            # Set up mapper to return action for KEY_KP0
            from numpad2midi.config import ActionType, MidiAction

            test_action = MidiAction(
                type=ActionType.PROGRAM_CHANGE, channel=0, program=5
            )
            mock_mapper_instance.get_action.return_value = test_action

            service = Service(config)

            # Simulate key press
            service._on_key_press("KEY_KP0")

            # Verify mapper was queried
            mock_mapper_instance.get_action.assert_called_once_with("KEY_KP0")

            # Verify MIDI action was sent
            mock_midi_instance.send_action.assert_called_once_with(test_action)

        finally:
            config_file.unlink()

    @patch("numpad2midi.service.Mapper")
    @patch("numpad2midi.service.MidiHandler")
    @patch("numpad2midi.service.InputHandler")
    def test_context_manager_usage(
        self, mock_input_handler: Mock, mock_midi_handler: Mock, mock_mapper: Mock
    ) -> None:
        """Test using service as context manager."""
        config_file = self._create_test_config_file()

        try:
            config = load_config(config_file)

            mock_input_instance = Mock()
            mock_midi_instance = Mock()
            mock_input_handler.return_value = mock_input_instance
            mock_midi_handler.return_value = mock_midi_instance

            # Use service in context manager
            with Service(config) as service:
                service.start(grab_device=False)
                assert mock_input_instance.start_listening.called

            # Verify cleanup was called
            mock_input_instance.stop.assert_called_once()
            mock_input_instance.close.assert_called_once()
            mock_midi_instance.close.assert_called_once()

        finally:
            config_file.unlink()

    def test_default_config_is_valid(self) -> None:
        """Test that the default config file is valid."""
        default_config = Path("config/default.yaml")

        if not default_config.exists():
            pytest.skip("Default config not found")

        config = load_config(default_config)

        assert config.device is not None
        assert config.midi is not None
        assert len(config.mappings) > 0

    def test_example_config_is_valid(self) -> None:
        """Test that the example config file is valid."""
        example_config = Path("config/example.yaml")

        if not example_config.exists():
            pytest.skip("Example config not found")

        config = load_config(example_config)

        assert config.device is not None
        assert config.midi is not None
        assert len(config.mappings) > 0
