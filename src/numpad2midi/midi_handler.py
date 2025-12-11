"""MIDI output handler for sending MIDI messages."""

import logging
from typing import Optional

import rtmidi

from numpad2midi.config import ActionType, MidiAction

logger = logging.getLogger(__name__)


class MidiError(Exception):
    """MIDI-related errors."""

    pass


class MidiHandler:
    """
    Handles MIDI output operations.

    Supports both virtual and physical MIDI ports and can send
    program changes, control changes, note on/off messages.
    """

    def __init__(self, port_name: str, virtual_port: bool = True) -> None:
        """
        Initialize MIDI handler.

        Args:
            port_name: Name of the MIDI port
            virtual_port: If True, create virtual port; if False, connect to physical port

        Raises:
            MidiError: If MIDI initialization fails or port not found
        """
        self.port_name = port_name
        self.virtual_port = virtual_port
        self._midiout: Optional[rtmidi.MidiOut] = None

        try:
            self._midiout = rtmidi.MidiOut()

            if virtual_port:
                self._midiout.open_virtual_port(port_name)
                logger.info(f"Opened virtual MIDI port: {port_name}")
            else:
                self._open_physical_port(port_name)

        except Exception as e:
            raise MidiError(f"Failed to initialize MIDI handler: {e}")

    def _open_physical_port(self, port_name: str) -> None:
        """
        Open a physical MIDI port by name.

        Args:
            port_name: Name of the port to open

        Raises:
            MidiError: If port not found
        """
        if self._midiout is None:
            raise MidiError("MIDI output not initialized")

        available_ports = self._midiout.get_ports()

        try:
            port_index = available_ports.index(port_name)
            self._midiout.open_port(port_index)
            logger.info(f"Opened physical MIDI port: {port_name}")
        except ValueError:
            available = ", ".join(available_ports) if available_ports else "none"
            raise MidiError(
                f"MIDI port '{port_name}' not found. Available ports: {available}"
            )

    def send_action(self, action: MidiAction) -> None:
        """
        Send a MIDI action.

        Args:
            action: MidiAction to send

        Raises:
            MidiError: If sending fails
        """
        if self._midiout is None:
            raise MidiError("MIDI output not initialized")

        try:
            message = self._build_message(action)
            self._midiout.send_message(message)
            logger.debug(f"Sent MIDI message: {message} for action type {action.type}")
        except Exception as e:
            raise MidiError(f"Failed to send MIDI message: {e}")

    def _build_message(self, action: MidiAction) -> list[int]:
        """
        Build MIDI message bytes from action.

        Args:
            action: MidiAction to convert

        Returns:
            List of MIDI message bytes
        """
        channel = action.channel

        if action.type == ActionType.PROGRAM_CHANGE:
            # Program change: 0xC0 + channel, program number
            return [0xC0 | channel, action.program or 0]

        elif action.type == ActionType.CONTROL_CHANGE:
            # Control change: 0xB0 + channel, controller, value
            return [0xB0 | channel, action.controller or 0, action.value or 0]

        elif action.type == ActionType.NOTE_ON:
            # Note on: 0x90 + channel, note, velocity
            return [0x90 | channel, action.note or 0, action.velocity or 0]

        elif action.type == ActionType.NOTE_OFF:
            # Note off: 0x80 + channel, note, velocity
            return [0x80 | channel, action.note or 0, action.velocity or 0]

        else:
            raise MidiError(f"Unknown action type: {action.type}")

    def is_open(self) -> bool:
        """
        Check if MIDI port is open.

        Returns:
            True if port is open, False otherwise
        """
        if self._midiout is None:
            return False
        return self._midiout.is_port_open()

    def close(self) -> None:
        """Close the MIDI port."""
        if self._midiout is not None:
            try:
                self._midiout.close_port()
                logger.info(f"Closed MIDI port: {self.port_name}")
            except Exception as e:
                logger.warning(f"Error closing MIDI port: {e}")

    def __enter__(self) -> "MidiHandler":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Context manager exit."""
        self.close()
