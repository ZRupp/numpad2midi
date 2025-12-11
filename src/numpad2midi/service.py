"""Main service orchestrator for numpad2midi."""

import logging
from typing import Optional

from numpad2midi.config import Config
from numpad2midi.input_handler import InputHandler
from numpad2midi.mapper import Mapper
from numpad2midi.midi_handler import MidiHandler

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Service-related errors."""

    pass


class Service:
    """
    Main service that orchestrates input handling, mapping, and MIDI output.

    Ties together InputHandler, Mapper, and MidiHandler to create a complete
    numpad-to-MIDI translation service.
    """

    def __init__(self, config: Config) -> None:
        """
        Initialize the service.

        Args:
            config: Configuration object

        Raises:
            ServiceError: If initialization fails
        """
        self.config = config
        self._input_handler: Optional[InputHandler] = None
        self._midi_handler: Optional[MidiHandler] = None
        self._mapper: Optional[Mapper] = None

        try:
            # Initialize MIDI handler
            self._midi_handler = MidiHandler(
                port_name=config.midi.port_name,
                virtual_port=config.midi.virtual_port,
            )

            # Initialize input handler
            if config.device.path:
                self._input_handler = InputHandler(device_path=config.device.path)
            else:
                self._input_handler = InputHandler(device_name=config.device.name)

            # Initialize mapper
            self._mapper = Mapper(config.mappings)

            logger.info("Service initialized successfully")

        except Exception as e:
            self.stop()
            raise ServiceError(f"Failed to initialize service: {e}")

    def _on_key_press(self, key: str) -> None:
        """
        Handle key press event.

        Args:
            key: Key name that was pressed
        """
        if self._mapper is None or self._midi_handler is None:
            logger.error("Service not properly initialized")
            return

        action = self._mapper.get_action(key)

        if action is None:
            logger.debug(f"No mapping for key: {key}")
            return

        try:
            self._midi_handler.send_action(action)
            logger.info(f"Key {key} triggered {action.type} action")
        except Exception as e:
            logger.error(f"Failed to send MIDI action for key {key}: {e}")

    def start(self, grab_device: bool = False) -> None:
        """
        Start the service.

        Args:
            grab_device: If True, grab input device for exclusive access
        """
        if self._input_handler is None:
            raise ServiceError("Input handler not initialized")

        logger.info("Starting numpad2midi service...")
        self._input_handler.start_listening(
            callback=self._on_key_press,
            grab=grab_device,
        )
        logger.info("Service started successfully")

    def stop(self) -> None:
        """Stop the service and clean up resources."""
        logger.info("Stopping numpad2midi service...")

        if self._input_handler:
            try:
                self._input_handler.stop()
                self._input_handler.close()
            except Exception as e:
                logger.warning(f"Error stopping input handler: {e}")

        if self._midi_handler:
            try:
                self._midi_handler.close()
            except Exception as e:
                logger.warning(f"Error closing MIDI handler: {e}")

        logger.info("Service stopped")

    def __enter__(self) -> "Service":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Context manager exit."""
        self.stop()
