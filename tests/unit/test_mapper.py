"""Tests for mapper module."""

from unittest.mock import Mock

import pytest

from numpad2midi.config import ActionType, KeyMapping, MidiAction
from numpad2midi.mapper import Mapper


class TestMapper:
    """Tests for Mapper class."""

    def test_init_with_mappings(self) -> None:
        """Test initialization with key mappings."""
        action1 = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=0)
        action2 = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=1)
        mappings = [
            KeyMapping(key="KEY_KP0", action=action1),
            KeyMapping(key="KEY_KP1", action=action2),
        ]

        mapper = Mapper(mappings)

        assert len(mapper._key_map) == 2
        assert mapper._key_map["KEY_KP0"] == action1
        assert mapper._key_map["KEY_KP1"] == action2

    def test_get_action_for_mapped_key(self) -> None:
        """Test getting action for a mapped key."""
        action = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=5)
        mappings = [KeyMapping(key="KEY_KP0", action=action)]
        mapper = Mapper(mappings)

        result = mapper.get_action("KEY_KP0")

        assert result == action

    def test_get_action_for_unmapped_key(self) -> None:
        """Test getting action for an unmapped key returns None."""
        action = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=0)
        mappings = [KeyMapping(key="KEY_KP0", action=action)]
        mapper = Mapper(mappings)

        result = mapper.get_action("KEY_KP9")

        assert result is None

    def test_has_mapping(self) -> None:
        """Test checking if key has mapping."""
        action = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=0)
        mappings = [KeyMapping(key="KEY_KP0", action=action)]
        mapper = Mapper(mappings)

        assert mapper.has_mapping("KEY_KP0") is True
        assert mapper.has_mapping("KEY_KP9") is False

    def test_get_all_mapped_keys(self) -> None:
        """Test getting list of all mapped keys."""
        action1 = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=0)
        action2 = MidiAction(type=ActionType.CONTROL_CHANGE, channel=0, controller=64, value=127)
        mappings = [
            KeyMapping(key="KEY_KP0", action=action1),
            KeyMapping(key="KEY_KP1", action=action2),
        ]
        mapper = Mapper(mappings)

        keys = mapper.get_mapped_keys()

        assert set(keys) == {"KEY_KP0", "KEY_KP1"}

    def test_empty_mappings(self) -> None:
        """Test mapper with empty mappings list."""
        mapper = Mapper([])

        assert len(mapper._key_map) == 0
        assert mapper.get_action("KEY_KP0") is None
        assert mapper.has_mapping("KEY_KP0") is False
        assert mapper.get_mapped_keys() == []

    def test_multiple_action_types(self) -> None:
        """Test mapper with multiple action types."""
        pc_action = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=1)
        cc_action = MidiAction(
            type=ActionType.CONTROL_CHANGE, channel=0, controller=7, value=100
        )
        note_action = MidiAction(type=ActionType.NOTE_ON, channel=0, note=60, velocity=100)

        mappings = [
            KeyMapping(key="KEY_KP0", action=pc_action),
            KeyMapping(key="KEY_KP1", action=cc_action),
            KeyMapping(key="KEY_KP2", action=note_action),
        ]
        mapper = Mapper(mappings)

        assert mapper.get_action("KEY_KP0") == pc_action
        assert mapper.get_action("KEY_KP1") == cc_action
        assert mapper.get_action("KEY_KP2") == note_action

    def test_case_sensitive_keys(self) -> None:
        """Test that key names are case sensitive."""
        action = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=0)
        mappings = [KeyMapping(key="KEY_KP0", action=action)]
        mapper = Mapper(mappings)

        assert mapper.has_mapping("KEY_KP0") is True
        assert mapper.has_mapping("key_kp0") is False
        assert mapper.has_mapping("KEY_kp0") is False
