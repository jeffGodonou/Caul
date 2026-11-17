"""Caul configuration defaults and environment-variable validation."""

import logging
import math
import os
from dataclasses import dataclass
from typing import Optional


MODEL_FOLDER_NAME = "vosk-model-small-en-us-0.15"


def _default_model_path():
    """Locate the Vosk model beside the module or in the installed data folder."""
    beside_module = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "models", MODEL_FOLDER_NAME
    )
    if os.path.isdir(beside_module):
        return beside_module
    # Installed builds may keep the model in the user's writable data directory.
    data_root = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(data_root, "Caul", "models", MODEL_FOLDER_NAME)


DEFAULT_VOSK_MODEL = _default_model_path()


@dataclass(frozen=True)
class Settings:
    microphone_device: Optional[int] = None
    listen_timeout: float = 5
    phrase_time_limit: float = 8
    sample_rate: int = 16000
    log_level: int = logging.WARNING
    vosk_model: str = DEFAULT_VOSK_MODEL


def load_settings(environ=None):
    """Read and validate optional Caul settings from environment variables."""
    environ = os.environ if environ is None else environ

    def positive_number(name, default, convert):
        value = environ.get(name)
        if value is None:
            return default
        try:
            parsed = convert(value)
        except ValueError as error:
            raise ValueError(name + " must be a positive number.") from error
        if parsed <= 0 or not math.isfinite(parsed):
            raise ValueError(name + " must be a positive finite number.")
        return parsed

    device_value = environ.get("CAUL_MICROPHONE_DEVICE", "").strip()
    try:
        microphone_device = int(device_value) if device_value else None
    except ValueError as error:
        raise ValueError("CAUL_MICROPHONE_DEVICE must be a device number.") from error
    if microphone_device is not None and microphone_device < 0:
        raise ValueError("CAUL_MICROPHONE_DEVICE must not be negative.")

    level_name = environ.get("CAUL_LOG_LEVEL", "WARNING").upper()
    log_level = logging.getLevelName(level_name)
    if not isinstance(log_level, int):
        raise ValueError("CAUL_LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR, or CRITICAL.")

    return Settings(
        microphone_device=microphone_device,
        listen_timeout=positive_number("CAUL_LISTEN_TIMEOUT", 5, float),
        phrase_time_limit=positive_number("CAUL_PHRASE_TIME_LIMIT", 8, float),
        sample_rate=positive_number("CAUL_SAMPLE_RATE", 16000, int),
        log_level=log_level,
        vosk_model=environ.get("CAUL_VOSK_MODEL", DEFAULT_VOSK_MODEL),
    )
