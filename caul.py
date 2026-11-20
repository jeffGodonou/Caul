"""Application entry point and compatibility exports for Caul's features."""

import logging
import os
import random
import sys

# Keep these imports available from ``caul`` for existing callers and tests.
from caul_alerts import AlertManager
from caul_audio import MicrophoneError, _recognize, _record, speak
from caul_calendar import (
    CALENDARS,
    CALENDAR_ALIASES,
    _calendar_date,
    _calendar_request,
    _calendar_time,
    _event_url,
    _prepare_calendar_event,
    _spoken_number,
)
from caul_commands import respond as _respond
from caul_math import _format_number, calculate
from caul_settings import (
    DEFAULT_VOSK_MODEL,
    MODEL_FOLDER_NAME,
    Settings,
    _default_model_path,
    load_settings,
)


logger = logging.getLogger("caul")
_active_alert_manager = None


def listen(settings=None):
    """Listen once and return recognized words, or None if they were unclear."""
    from caul_audio import listen as _listen

    # Pass through the public module-level functions so callers can replace them.
    on_wait = _active_alert_manager.check_due if _active_alert_manager else None
    return _listen(
        settings,
        recorder=_record,
        recognizer=_recognize,
        speaker=speak,
        on_wait=on_wait,
    )


def respond(
    command,
    speaker=speak,
    clock=None,
    browser=None,
    app_launcher=None,
    random_choice=random.choice,
    listener=None,
    alert_manager=None,
):
    """Handle supported commands and return False when asked to exit."""
    return _respond(
        command,
        speaker=speaker,
        clock=clock,
        browser=browser,
        app_launcher=app_launcher,
        random_choice=random_choice,
        listener=listener if listener is not None else listen,
        calculate_function=calculate,
        format_number=_format_number,
        calendar_request=_calendar_request,
        prepare_event=_prepare_calendar_event,
        calendars=CALENDARS,
        calendar_aliases=CALENDAR_ALIASES,
        alert_manager=alert_manager or _active_alert_manager,
    )


def main(settings=None, alert_manager=None):
    global _active_alert_manager
    previous_alert_manager = _active_alert_manager
    try:
        settings = settings or load_settings()
        alert_manager = alert_manager or AlertManager(speak)
        _active_alert_manager = alert_manager
        alert_manager.check_due()
        logging.basicConfig(
            level=settings.log_level,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
        speak("Caul is ready. Say hello, or say goodbye to stop.")
        while True:
            command = listen(settings)
            if command is not None and not respond(
                command,
                listener=lambda: listen(settings),
                alert_manager=alert_manager,
            ):
                break
    except KeyboardInterrupt:
        speak("Goodbye!")
    except (OSError, ImportError, RuntimeError, ValueError) as error:
        logger.exception("Caul could not start or access a required resource.")
        print("Caul setup error:", error, file=sys.stderr)
        print(
            "Check the setup and microphone troubleshooting steps in README.md.",
            file=sys.stderr,
        )
    finally:
        _active_alert_manager = previous_alert_manager


if __name__ == "__main__":
    main()
