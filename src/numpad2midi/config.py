"""Configuration management for numpad2midi service."""

import logging
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Configuration related errors."""

    pass


class ActionType(str, Enum):
    """MIDI action types."""

    PROGRAM_CHANGE = "program_change"
    CONTROL_CHANGE = "control_change"
    NOTE_ON = "note_on"
    NOTE_OFF = "note_off"


class MidiAction(BaseModel):
    """MIDI action configuration."""

    type: ActionType
    channel: int = Field(ge=0, le=15, description="MIDI channel (0-15)")
    program: Optional[int] = Field(None, ge=0, le=127, description="Program number (0-127)")
    controller: Optional[int] = Field(
        None, ge=0, le=127, description="Controller number (0-127)"
    )
    value: Optional[int] = Field(None, ge=0, le=127, description="Controller value (0-127)")
    note: Optional[int] = Field(None, ge=0, le=127, description="MIDI note (0-127)")
    velocity: Optional[int] = Field(None, ge=0, le=127, description="Note velocity (0-127)")

    @model_validator(mode="after")
    def validate_action_fields(self) -> "MidiAction":
        """Validate that required fields for each action type are present."""
        if self.type == ActionType.PROGRAM_CHANGE:
            if self.program is None:
                raise ValueError("program_change requires 'program' field")
        elif self.type == ActionType.CONTROL_CHANGE:
            if self.controller is None or self.value is None:
                raise ValueError("control_change requires 'controller' and 'value' fields")
        elif self.type in (ActionType.NOTE_ON, ActionType.NOTE_OFF):
            if self.note is None or self.velocity is None:
                raise ValueError(f"{self.type} requires 'note' and 'velocity' fields")
        return self


class KeyMapping(BaseModel):
    """Mapping of a key to a MIDI action."""

    key: str = Field(min_length=1, description="Linux input event key code (e.g., KEY_KP0)")
    action: MidiAction

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        """Validate key is not empty."""
        if not v or not v.strip():
            raise ValueError("Key cannot be empty")
        return v


class DeviceConfig(BaseModel):
    """Input device configuration."""

    name: Optional[str] = Field(None, description="Device name pattern for auto-detection")
    path: Optional[str] = Field(None, description="Explicit device path (e.g., /dev/input/event0)")


class MidiConfig(BaseModel):
    """MIDI output configuration."""

    port_name: str = Field(min_length=1, description="MIDI port name")
    virtual_port: bool = Field(True, description="Create virtual MIDI port")


class Config(BaseModel):
    """Main configuration model."""

    device: DeviceConfig
    midi: MidiConfig
    mappings: list[KeyMapping] = Field(min_length=1, description="Key to MIDI mappings")

    @model_validator(mode="after")
    def validate_unique_keys(self) -> "Config":
        """Ensure all mapped keys are unique."""
        keys = [m.key for m in self.mappings]
        if len(keys) != len(set(keys)):
            duplicates = [k for k in keys if keys.count(k) > 1]
            raise ValueError(f"Duplicate key mappings found: {set(duplicates)}")
        return self


def load_config(config_path: Path) -> Config:
    """
    Load and validate configuration from YAML file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Validated Config object

    Raises:
        ConfigError: If file not found, parsing fails, or validation fails
    """
    if not config_path.exists():
        raise ConfigError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse YAML configuration: {e}")
    except Exception as e:
        raise ConfigError(f"Failed to read configuration file: {e}")

    try:
        config = Config(**data)
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except Exception as e:
        raise ConfigError(f"Configuration validation failed: {e}")
