# Development Guide

This guide covers development setup, architecture, testing, and contributing to numpad2midi.

## Table of Contents

- [Development Setup](#development-setup)
- [Architecture](#architecture)
- [Testing](#testing)
- [Code Standards](#code-standards)
- [Contributing](#contributing)

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- Linux system (for evdev)
- Virtual environment (recommended)

### Initial Setup

```bash
# Clone repository
git clone https://github.com/ZRupp/numpad2midi.git
cd numpad2midi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Or install from requirements
pip install -r requirements-dev.txt
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=numpad2midi --cov-report=html

# Run specific test file
pytest tests/unit/test_config.py

# Run with verbose output
pytest -v

# Run and watch for changes (requires pytest-watch)
ptw
```

### Code Quality Tools

```bash
# Format code with black
black src/ tests/

# Lint with flake8
flake8 src/ tests/

# Type check with mypy
mypy src/

# Run all checks
black src/ tests/ && flake8 src/ tests/ && mypy src/ && pytest
```

## Architecture

### Overview

```
┌─────────────┐
│   CLI       │  __main__.py - Entry point, argument parsing
└─────┬───────┘
      │
┌─────▼───────┐
│  Service    │  service.py - Orchestrates components
└─────┬───────┘
      │
      ├─────────────┐─────────────┐
      │             │             │
┌─────▼──────┐ ┌───▼────┐  ┌────▼─────┐
│InputHandler│ │ Mapper │  │MidiHandler│
└─────┬──────┘ └───┬────┘  └────┬──────┘
      │            │             │
┌─────▼──────┐ ┌───▼────┐  ┌────▼──────┐
│   evdev    │ │ Config │  │  rtmidi   │
└────────────┘ └────────┘  └───────────┘
```

### Components

#### 1. Configuration (`config.py`)

- **Purpose**: Load and validate YAML configuration
- **Technology**: Pydantic for validation
- **Key Classes**:
  - `Config`: Main configuration model
  - `DeviceConfig`: Input device configuration
  - `MidiConfig`: MIDI output configuration
  - `KeyMapping`: Key-to-action mappings
  - `MidiAction`: MIDI action definitions

**Design Decisions**:
- Use Pydantic for type-safe validation
- Fail fast on invalid config
- Support both device paths and names for flexibility

#### 2. Input Handler (`input_handler.py`)

- **Purpose**: Capture keyboard events from input devices
- **Technology**: python-evdev
- **Key Features**:
  - Auto-detection by device name
  - Background thread for event loop
  - Optional device grabbing for exclusive access
  - Callback-based architecture

**Design Decisions**:
- Thread-based to avoid blocking main thread
- Filter for key-down events only (no repeats)
- Support both name-based and path-based device selection

#### 3. MIDI Handler (`midi_handler.py`)

- **Purpose**: Send MIDI messages
- **Technology**: python-rtmidi
- **Key Features**:
  - Virtual and physical port support
  - Multiple message types (PC, CC, Note On/Off)
  - Context manager for cleanup

**Design Decisions**:
- Simple, focused interface
- Build MIDI bytes manually for clarity
- Graceful error handling

#### 4. Mapper (`mapper.py`)

- **Purpose**: Map key names to MIDI actions
- **Key Features**:
  - Fast dictionary-based lookup
  - Simple, stateless design

**Design Decisions**:
- Dictionary for O(1) lookup
- No complex logic, just data mapping
- Immutable after construction

#### 5. Service (`service.py`)

- **Purpose**: Coordinate all components
- **Key Features**:
  - Initialize and manage lifecycle
  - Connect input events to MIDI output
  - Graceful shutdown
  - Error handling and logging

**Design Decisions**:
- Single responsibility: coordinate components
- Context manager support
- Comprehensive logging

#### 6. CLI (`__main__.py`)

- **Purpose**: Command-line interface
- **Key Features**:
  - Argument parsing
  - Signal handling (SIGINT, SIGTERM)
  - Logging configuration

**Design Decisions**:
- Keep simple, delegate to Service
- Proper signal handling for daemon use
- Clear error messages

## Testing

### Test Structure

```
tests/
├── unit/           # Unit tests for individual components
│   ├── test_config.py
│   ├── test_input_handler.py
│   ├── test_mapper.py
│   ├── test_midi_handler.py
│   └── test_service.py
└── integration/    # Integration tests
    └── test_end_to_end.py
```

### Testing Philosophy

1. **Test-Driven Development**: Write tests first, then implementation
2. **High Coverage**: Target 80%+ coverage
3. **Mock External Dependencies**: Use mocks for evdev and rtmidi
4. **Test Behavior, Not Implementation**: Focus on what, not how

### Writing Tests

#### Unit Test Example

```python
from unittest.mock import Mock, patch
import pytest
from numpad2midi.mapper import Mapper

class TestMapper:
    def test_get_action_for_mapped_key(self) -> None:
        """Test getting action for a mapped key."""
        action = MidiAction(type=ActionType.PROGRAM_CHANGE, channel=0, program=5)
        mappings = [KeyMapping(key="KEY_KP0", action=action)]
        mapper = Mapper(mappings)

        result = mapper.get_action("KEY_KP0")

        assert result == action
```

#### Integration Test Example

```python
def test_full_service_lifecycle(self) -> None:
    """Test complete service lifecycle."""
    config = load_config("config/default.yaml")

    with Service(config) as service:
        service.start(grab_device=False)
        # Service is running

    # Service automatically cleaned up
```

### Mocking Strategy

- **evdev**: Mock `InputDevice` and `ecodes`
- **rtmidi**: Mock `MidiOut`
- **Files**: Use `tempfile` for config files

## Code Standards

### Style Guide

- **PEP 8**: Follow Python style guide
- **Line Length**: Max 100 characters
- **Formatting**: Use `black` for consistent formatting
- **Linting**: Use `flake8` for style checking
- **Type Hints**: Full type annotations (checked by `mypy`)

### Documentation

- **Docstrings**: Google-style for public APIs
- **Comments**: Only for non-obvious logic
- **README**: Keep user documentation updated
- **DEVELOPMENT**: Keep developer documentation updated

### Type Hints

```python
# Good
def get_action(self, key: str) -> Optional[MidiAction]:
    """Get MIDI action for a key."""
    return self._key_map.get(key)

# Bad
def get_action(self, key):
    return self._key_map.get(key)
```

### Error Handling

- **Custom Exceptions**: Use for domain errors
- **Logging**: Log errors before raising
- **Graceful Degradation**: Continue when possible

```python
# Good
try:
    self._midi_handler.send_action(action)
except Exception as e:
    logger.error(f"Failed to send MIDI: {e}")
    # Continue processing other keys

# Bad
self._midi_handler.send_action(action)  # Crashes on error
```

## Contributing

### Workflow

1. **Fork** the repository
2. **Clone** your fork
3. **Create branch**: `git checkout -b feature/my-feature`
4. **Make changes** following code standards
5. **Write tests** for new functionality
6. **Run tests**: `pytest`
7. **Format code**: `black src/ tests/`
8. **Commit**: Clear, descriptive messages
9. **Push** to your fork
10. **Create Pull Request**

### Commit Messages

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Examples**:
```
feat(config): add support for custom MIDI channels

Add channel configuration per mapping instead of global setting.
This allows more flexible device control.

Closes #42
```

```
fix(input): handle device disconnection gracefully

Previously crashed on device disconnect. Now logs error and
continues running with attempt to reconnect.
```

### Pull Request Guidelines

- **Description**: Clear explanation of changes
- **Tests**: All tests passing
- **Coverage**: Maintain or improve coverage
- **Documentation**: Update if needed
- **One Feature**: One logical change per PR

### Code Review

PRs will be reviewed for:
- Correctness
- Test coverage
- Code style
- Documentation
- Performance
- Security

## Project Maintenance

### Release Process

1. Update version in `src/numpad2midi/__init__.py`
2. Update `CHANGELOG.md`
3. Run full test suite
4. Create git tag: `git tag v0.1.0`
5. Push tag: `git push origin v0.1.0`
6. Create GitHub release

### Version Scheme

Follow Semantic Versioning (SemVer):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

## Debugging

### Enable Debug Logging

```bash
numpad2midi --verbose config.yaml
```

### Test MIDI Output

```bash
# Monitor MIDI port
aseqdump -p "numpad2midi"

# List MIDI connections
aconnect -l
```

### Test Input Device

```bash
# Test device events
sudo evtest /dev/input/event0

# List input devices
ls -l /dev/input/by-id/
```

### Common Issues

**ImportError**: Check PYTHONPATH and virtual environment
**PermissionError**: Ensure user in `input` group
**MidiError**: Check ALSA/JACK is running

## Resources

- [evdev Documentation](https://python-evdev.readthedocs.io/)
- [python-rtmidi Documentation](https://spotlightkid.github.io/python-rtmidi/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [MIDI Specification](https://www.midi.org/specifications)
- [pytest Documentation](https://docs.pytest.org/)

## Questions?

- **Bug Reports**: [GitHub Issues](https://github.com/ZRupp/numpad2midi/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/ZRupp/numpad2midi/discussions)
- **General Questions**: [GitHub Discussions](https://github.com/ZRupp/numpad2midi/discussions)

---

Thank you for contributing to numpad2midi!
