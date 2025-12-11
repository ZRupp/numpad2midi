"""Command-line interface for numpad2midi service."""

import argparse
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

from numpad2midi.config import ConfigError, load_config
from numpad2midi.discover import list_input_devices, verify_device, find_device_interactive
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
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command (default)
    run_parser = subparsers.add_parser(
        "run",
        help="Run the numpad2midi service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  numpad2midi run config/default.yaml
  numpad2midi run --verbose --grab config/default.yaml
  numpad2midi run --no-grab ~/.config/numpad2midi.yaml
        """,
    )

    run_parser.add_argument(
        "config",
        type=Path,
        help="Path to configuration YAML file",
    )

    run_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )

    run_parser.add_argument(
        "-g",
        "--grab",
        action="store_true",
        default=False,
        help="Grab input device for exclusive access",
    )

    run_parser.add_argument(
        "--no-grab",
        action="store_true",
        help="Do not grab input device (allows sharing with other apps)",
    )

    # List devices command
    list_parser = subparsers.add_parser(
        "list-devices",
        help="List all available input devices",
        aliases=["list", "ls"],
    )

    list_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed device information",
    )

    # Test device command
    test_parser = subparsers.add_parser(
        "test-device",
        help="Test an input device by showing key presses",
        aliases=["test"],
    )

    test_parser.add_argument(
        "device",
        nargs="?",
        help="Device path to test (e.g., /dev/input/event0)",
    )

    test_parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=5,
        help="How long to listen for events (seconds, default: 5)",
    )

    # For backwards compatibility, allow running without subcommand
    # If first arg is a file path, treat as "run" command
    parser.add_argument(
        "config_compat",
        type=Path,
        nargs="?",
        help=argparse.SUPPRESS,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    parser.add_argument(
        "-g",
        "--grab",
        action="store_true",
        default=False,
        help=argparse.SUPPRESS,
    )

    parser.add_argument(
        "--no-grab",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    return parser.parse_args()


def cmd_run(args: argparse.Namespace) -> int:
    """
    Run the service.

    Args:
        args: Parsed arguments

    Returns:
        Exit code
    """
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


def cmd_list_devices(args: argparse.Namespace) -> int:
    """
    List available input devices.

    Args:
        args: Parsed arguments

    Returns:
        Exit code
    """
    try:
        list_input_devices(verbose=args.verbose)
        return 0
    except Exception as e:
        print(f"Error listing devices: {e}")
        return 1


def cmd_test_device(args: argparse.Namespace) -> int:
    """
    Test an input device.

    Args:
        args: Parsed arguments

    Returns:
        Exit code
    """
    device_path = args.device

    # If no device specified, show interactive selector
    if not device_path:
        device_path = find_device_interactive()
        if not device_path:
            return 1

    try:
        verify_device(device_path, timeout=args.timeout)
        return 0
    except Exception as e:
        print(f"Error testing device: {e}")
        return 1


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    args = parse_args()

    # Handle backwards compatibility (no subcommand)
    if args.command is None:
        if args.config_compat:
            # Old style: numpad2midi config.yaml
            args.command = "run"
            args.config = args.config_compat
        else:
            # No arguments, show help
            print("Error: Missing command or configuration file\n")
            print("Usage:")
            print("  numpad2midi run <config.yaml>       Run the service")
            print("  numpad2midi list-devices            List available devices")
            print("  numpad2midi test-device [path]      Test a device")
            print("\nFor more help: numpad2midi --help")
            return 1

    # Dispatch to command handlers
    if args.command == "run":
        return cmd_run(args)
    elif args.command in ("list-devices", "list", "ls"):
        return cmd_list_devices(args)
    elif args.command in ("test-device", "test"):
        return cmd_test_device(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
