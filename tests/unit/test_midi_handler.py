"""Tests for MIDI handler module."""

from unittest.mock import Mock, patch, MagicMock

import pytest

from numpad2midi.config import ActionType, MidiAction
from numpad2midi.midi_handler import MidiHandler, MidiError


class TestMidiHandler:
    """Tests for MidiHandler class."""

    @patch("numpad2midi.midi_handler.rtmidi")
    def test_init_virtual_port(self, mock_rtmidi: Mock) -> None:
        """Test initialization with virtual port."""
        mock_midiout = Mock()
        mock_rtmidi.MidiOut.return_value = mock_midiout

        handler = MidiHandler(port_name="test_port", virtual_port=True)

        mock_rtmidi.MidiOut.assert_called_once()
        mock_midiout.open_virtual_port.assert_called_once_with("test_port")
        assert handler.port_name == "test_port"

    @patch("numpad2midi.midi_handler.rtmidi")
    def test_init_physical_port_by_name(self, mock_rtmidi: Mock) -> None:
        """Test initialization with physical port by name."""
        mock_midiout = Mock()
        mock_midiout.get_ports.return_value = ["Port1", "test_port", "Port2"]
        mock_rtmidi.MidiOut.return_value = mock_midiout

        handler = MidiHandler(port_name="test_port", virtual_port=False)

        mock_midiout.open_port.assert_called_once_with(1)
        assert handler.port_name == "test_port"

    @patch("numpad2midi.midi_handler.rtmidi")
    def test_init_physical_port_not_found(self, mock_rtmidi: Mock) -> None:
        """Test initialization fails when physical port not found."""
        mock_midiout = Mock()
        mock_midiout.get_ports.return_value = ["Port1", "Port2"]
        mock_rtmidi.MidiOut.return_value = mock_midiout

        with pytest.raises(MidiError, match="MIDI port 'nonexistent' not found"):
            MidiHandler(port_name="nonexistent", virtual_port=False)

    @patch("numpad2midi.midi_handler.rtmidi")
    def test_init_error_handling(self, mock_rtmidi: Mock) -> None:
        """Test initialization error handling."""
        mock_rtmidi.MidiOut.side_effect = Exception("MIDI init failed")

        with pytest.raises(MidiError, match="Failed to initialize"):
            MidiHandler(port_name="test", virtual_port=True)

    @patch("numpad2midi.midi_handler.rtmidi")
    def test_send_program_change(self, mock_rtmidi: Mock) -> None:
        """Test sending program change message."""
        mock_midiout = Mock()
        mock_rtmidi.MidiOut.return_value = mock_midiout

        handler = MidiHandler(port_name="test", virtual_port=True)
        action = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=5)

        handler.send_action(action)

        mock_midiout.send_message.assert_called_once()
        message = mock_midiout.send_message.call_args[0][0]
        assert message == [0xC0, 5]  # Program change on channel 0, program 5

    @patch("numpad2midi.midi_handler.rtmidi")
    def test_send_program_change_different_channel(self, mock_rtmidi: Mock) -> None:
        """Test program change on different channel."""
        mock_midiout = Mock()
        mock_rtmidi.MidiOut.return_value = mock_midiout

        handler = MidiHandler(port_name="test", virtual_port=True)
        action = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=3, program=10)

        handler.send_action(action)

        message = mock_midiout.send_message.call_args[0][0]
        assert message == [0xC3, 10]  # Program change on channel 3

    @patch("numpad2midi.midi_handler.rtmidi")
    def test_send_control_change(self, mock_rtmidi: Mock) -> None:
        """Test sending control change message."""
        mock_midiout = Mock()
        mock_rtmidi.MidiOut.return_value = mock_midiout

        handler = MidiHandler(port_name="test", virtual_port=True)
        action = MidiAction(
            type=ActionType.CONTROL_CHANGE, channel=0, controller=64, value=127
        )

        handler.send_action(action)

        message = mock_midiout.send_message.call_args[0][0]
        assert message == [0xB0, 64, 127]  # CC on channel 0, controller 64, value 127

    @patch("numpad2midi.midi_handler.rtmidi")
    def test_send_note_on(self, mock_rtmidi: Mock) -> None:
        """Test sending note on message."""
        mock_midiout = Mock()
        mock_rtmidi.MidiOut.return_value = mock_midiout

        handler = MidiHandler(port_name="test", virtual_port=True)
        action = MidiAction(type=ActionType.NOTE_ON, channel=0, note=60, velocity=100)

        handler.send_action(action)

        message = mock_midiout.send_message.call_args[0][0]
        assert message == [0x90, 60, 100]  # Note on channel 0, note 60, velocity 100

    @patch("numpad2midi.midi_handler.rtmidi")
    def test_send_note_off(self, mock_rtmidi: Mock) -> None:
        """Test sending note off message."""
        mock_midiout = Mock()
        mock_rtmidi.MidiOut.return_value = mock_midiout

        handler = MidiHandler(port_name="test", virtual_port=True)
        action = MidiAction(type=ActionType.NOTE_OFF, channel=0, note=60, velocity=0)

        handler.send_action(action)

        message = mock_midiout.send_message.call_args[0][0]
        assert message == [0x80, 60, 0]  # Note off channel 0, note 60, velocity 0

    @patch("numpad2midi.midi_handler.rtmidi")
    def test_send_action_error_handling(self, mock_rtmidi: Mock) -> None:
        """Test error handling when sending MIDI message."""
        mock_midiout = Mock()
        mock_midiout.send_message.side_effect = Exception("Send failed")
        mock_rtmidi.MidiOut.return_value = mock_midiout

        handler = MidiHandler(port_name="test", virtual_port=True)
        action = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=0)

        with pytest.raises(MidiError, match="Failed to send"):
            handler.send_action(action)

    @patch("numpad2midi.midi_handler.rtmidi")
    def test_close(self, mock_rtmidi: Mock) -> None:
        """Test closing MIDI port."""
        mock_midiout = Mock()
        mock_rtmidi.MidiOut.return_value = mock_midiout

        handler = MidiHandler(port_name="test", virtual_port=True)
        handler.close()

        mock_midiout.close_port.assert_called_once()

    @patch("numpad2midi.midi_handler.rtmidi")
    def test_context_manager(self, mock_rtmidi: Mock) -> None:
        """Test using handler as context manager."""
        mock_midiout = Mock()
        mock_rtmidi.MidiOut.return_value = mock_midiout

        with MidiHandler(port_name="test", virtual_port=True) as handler:
            assert handler is not None

        mock_midiout.close_port.assert_called_once()

    @patch("numpad2midi.midi_handler.rtmidi")
    def test_is_open(self, mock_rtmidi: Mock) -> None:
        """Test checking if port is open."""
        mock_midiout = Mock()
        mock_midiout.is_port_open.return_value = True
        mock_rtmidi.MidiOut.return_value = mock_midiout

        handler = MidiHandler(port_name="test", virtual_port=True)

        assert handler.is_open() is True
        mock_midiout.is_port_open.assert_called_once()

    @patch("numpad2midi.midi_handler.rtmidi")
    def test_multiple_messages(self, mock_rtmidi: Mock) -> None:
        """Test sending multiple messages in sequence."""
        mock_midiout = Mock()
        mock_rtmidi.MidiOut.return_value = mock_midiout

        handler = MidiHandler(port_name="test", virtual_port=True)

        action1 = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=1)
        action2 = MidiAction(type=ActionType.CONTROL_CHANGE, channel=0, controller=7, value=100)
        action3 = MidiAction(type=ActionType.NOTE_ON, channel=0, note=60, velocity=100)

        handler.send_action(action1)
        handler.send_action(action2)
        handler.send_action(action3)

        assert mock_midiout.send_message.call_count == 3
