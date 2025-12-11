"""Tests for configuration module."""

import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml

from numpad2midi.config import (
    Config,
    DeviceConfig,
    MidiConfig,
    KeyMapping,
    MidiAction,
    ActionType,
    load_config,
    ConfigError,
)


class TestMidiAction:
    """Tests for MidiAction model."""

    def test_program_change_action(self) -> None:
        action = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=5)
        assert action.type == ActionType.PROGRAM_CHANGE
        assert action.channel == 0
        assert action.program == 5
        assert action.controller is None
        assert action.value is None

    def test_control_change_action(self) -> None:
        action = MidiAction(
            type=ActionType.CONTROL_CHANGE, channel=1, controller=64, value=127
        )
        assert action.type == ActionType.CONTROL_CHANGE
        assert action.channel == 1
        assert action.controller == 64
        assert action.value == 127

    def test_note_on_action(self) -> None:
        action = MidiAction(type=ActionType.NOTE_ON, channel=0, note=60, velocity=100)
        assert action.type == ActionType.NOTE_ON
        assert action.note == 60
        assert action.velocity == 100

    def test_note_off_action(self) -> None:
        action = MidiAction(type=ActionType.NOTE_OFF, channel=0, note=60, velocity=0)
        assert action.type == ActionType.NOTE_OFF
        assert action.note == 60
        assert action.velocity == 0

    def test_invalid_channel_range(self) -> None:
        with pytest.raises(ValueError):
            MidiAction(type=ActionType.PROGRAM_CHANGE, channel=16, program=0)

    def test_negative_channel(self) -> None:
        with pytest.raises(ValueError):
            MidiAction(type=ActionType.PROGRAM_CHANGE, channel=-1, program=0)


class TestKeyMapping:
    """Tests for KeyMapping model."""

    def test_valid_key_mapping(self) -> None:
        action = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=1)
        mapping = KeyMapping(key="KEY_KP0", action=action)
        assert mapping.key == "KEY_KP0"
        assert mapping.action == action

    def test_empty_key_rejected(self) -> None:
        action = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=1)
        with pytest.raises(ValueError):
            KeyMapping(key="", action=action)


class TestDeviceConfig:
    """Tests for DeviceConfig model."""

    def test_device_with_name(self) -> None:
        device = DeviceConfig(name="numpad")
        assert device.name == "numpad"
        assert device.path is None

    def test_device_with_path(self) -> None:
        device = DeviceConfig(path="/dev/input/event0")
        assert device.path == "/dev/input/event0"
        assert device.name is None

    def test_device_with_both(self) -> None:
        device = DeviceConfig(name="numpad", path="/dev/input/event0")
        assert device.name == "numpad"
        assert device.path == "/dev/input/event0"


class TestMidiConfig:
    """Tests for MidiConfig model."""

    def test_virtual_port_config(self) -> None:
        midi = MidiConfig(port_name="test_port", virtual_port=True)
        assert midi.port_name == "test_port"
        assert midi.virtual_port is True

    def test_physical_port_config(self) -> None:
        midi = MidiConfig(port_name="MIDI Port", virtual_port=False)
        assert midi.port_name == "MIDI Port"
        assert midi.virtual_port is False

    def test_default_values(self) -> None:
        midi = MidiConfig(port_name="default")
        assert midi.port_name == "default"
        assert midi.virtual_port is True


class TestConfig:
    """Tests for Config model."""

    def test_valid_config(self) -> None:
        device = DeviceConfig(name="numpad")
        midi = MidiConfig(port_name="numpad2midi")
        action = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=0)
        mappings = [KeyMapping(key="KEY_KP0", action=action)]

        config = Config(device=device, midi=midi, mappings=mappings)

        assert config.device == device
        assert config.midi == midi
        assert len(config.mappings) == 1
        assert config.mappings[0].key == "KEY_KP0"

    def test_empty_mappings_rejected(self) -> None:
        device = DeviceConfig(name="numpad")
        midi = MidiConfig(port_name="numpad2midi")

        with pytest.raises(ValueError):
            Config(device=device, midi=midi, mappings=[])

    def test_duplicate_keys_rejected(self) -> None:
        device = DeviceConfig(name="numpad")
        midi = MidiConfig(port_name="numpad2midi")
        action1 = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=0)
        action2 = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=1)
        mappings = [
            KeyMapping(key="KEY_KP0", action=action1),
            KeyMapping(key="KEY_KP0", action=action2),
        ]

        with pytest.raises(ValueError, match="Duplicate key"):
            Config(device=device, midi=midi, mappings=mappings)


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_valid_config(self) -> None:
        config_data = {
            "device": {"name": "numpad"},
            "midi": {"port_name": "numpad2midi", "virtual_port": True},
            "mappings": [
                {
                    "key": "KEY_KP0",
                    "action": {"type": "program_change", "channel": 0, "program": 0},
                },
                {
                    "key": "KEY_KP1",
                    "action": {
                        "type": "control_change",
                        "channel": 0,
                        "controller": 64,
                        "value": 127,
                    },
                },
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = load_config(Path(temp_path))
            assert config.device.name == "numpad"
            assert config.midi.port_name == "numpad2midi"
            assert len(config.mappings) == 2
            assert config.mappings[0].key == "KEY_KP0"
            assert config.mappings[1].key == "KEY_KP1"
        finally:
            Path(temp_path).unlink()

    def test_load_nonexistent_file(self) -> None:
        with pytest.raises(ConfigError, match="not found"):
            load_config(Path("/nonexistent/config.yaml"))

    def test_load_invalid_yaml(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content:\n  - broken")
            temp_path = f.name

        try:
            with pytest.raises(ConfigError, match="parse"):
                load_config(Path(temp_path))
        finally:
            Path(temp_path).unlink()

    def test_load_invalid_schema(self) -> None:
        config_data = {
            "device": {"name": "numpad"},
            "midi": {"port_name": "test"},
            "mappings": [],  # Empty mappings should fail validation
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(ConfigError, match="validation"):
                load_config(Path(temp_path))
        finally:
            Path(temp_path).unlink()

    def test_load_missing_required_fields(self) -> None:
        config_data = {
            "device": {"name": "numpad"},
            # Missing 'midi' field
            "mappings": [
                {
                    "key": "KEY_KP0",
                    "action": {"type": "program_change", "channel": 0, "program": 0},
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(ConfigError, match="validation"):
                load_config(Path(temp_path))
        finally:
            Path(temp_path).unlink()
