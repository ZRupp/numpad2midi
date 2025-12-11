"""Mapper for translating key presses to MIDI actions."""

import logging
from typing import Optional

from numpad2midi.config import KeyMapping, MidiAction

logger = logging.getLogger(__name__)


class Mapper:
    """
    Maps keyboard keys to MIDI actions.

    Provides fast lookup from key names to their corresponding MIDI actions.
    """

    def __init__(self, mappings: list[KeyMapping]) -> None:
        """
        Initialize mapper with key mappings.

        Args:
            mappings: List of KeyMapping objects
        """
        self._key_map: dict[str, MidiAction] = {}

        for mapping in mappings:
            self._key_map[mapping.key] = mapping.action

        logger.info(f"Initialized mapper with {len(self._key_map)} key mappings")

    def get_action(self, key: str) -> Optional[MidiAction]:
        """
        Get MIDI action for a key.

        Args:
            key: Key name (e.g., "KEY_KP0")

        Returns:
            MidiAction if key is mapped, None otherwise
        """
        return self._key_map.get(key)

    def has_mapping(self, key: str) -> bool:
        """
        Check if a key has a mapping.

        Args:
            key: Key name to check

        Returns:
            True if key is mapped, False otherwise
        """
        return key in self._key_map

    def get_mapped_keys(self) -> list[str]:
        """
        Get list of all mapped key names.

        Returns:
            List of key names that have mappings
        """
        return list(self._key_map.keys())
