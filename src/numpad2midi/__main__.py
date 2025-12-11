"""Command-line interface for numpad2midi service."""

import argparse
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

from numpad2midi.config import ConfigError, load_config
from numpad2midi.service import Service, ServiceError

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging.

    Args:
        verbose: If True, set DEBUG level; otherwise INFO
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Numpad to MIDI service for MODEP control",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  numpad2midi config/default.yaml
  numpad2midi --verbose --grab config/default.yaml
  numpad2midi --no-grab ~/.config/numpad2midi.yaml
        """,
    )

    parser.add_argument(
        "config",
        type=Path,
        help="Path to configuration YAML file",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )

    parser.add_argument(
        "-g",
        "--grab",
        action="store_true",
        default=False,
        help="Grab input device for exclusive access",
    )

    parser.add_argument(
        "--no-grab",
        action="store_true",
        help="Do not grab input device (allows sharing with other apps)",
    )

    return parser.parse_args()


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    args = parse_args()
    setup_logging(args.verbose)

    # Determine grab setting
    grab_device = args.grab and not args.no_grab

    logger.info(f"Starting numpad2midi v{__import__('numpad2midi').__version__}")
    logger.info(f"Loading configuration from: {args.config}")

    # Load configuration
    try:
        config = load_config(args.config)
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        return 1

    # Initialize service
    service: Optional[Service] = None
    try:
        service = Service(config)
    except ServiceError as e:
        logger.error(f"Service initialization error: {e}")
        return 1

    # Set up signal handlers for graceful shutdown
    def signal_handler(sig: int, frame) -> None:  # type: ignore
        logger.info(f"Received signal {sig}, shutting down...")
        if service:
            service.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start service
    try:
        logger.info(f"Device grab: {'enabled' if grab_device else 'disabled'}")
        service.start(grab_device=grab_device)
        logger.info("Service running. Press Ctrl+C to stop.")

        # Keep main thread alive
        signal.pause()

    except ServiceError as e:
        logger.error(f"Service error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1
    finally:
        if service:
            service.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
