import logging
import os
import random
import sys

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


def listen(settings=None):
    """Listen once and return recognized words, or None if they were unclear."""
    from caul_audio import listen as _listen

    return _listen(settings, recorder=_record, recognizer=_recognize, speaker=speak)


def respond(
    command,
    speaker=speak,
    clock=None,
    browser=None,
    app_launcher=None,
    random_choice=random.choice,
    listener=None,
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
    )


def main(settings=None):
    try:
        settings = settings or load_settings()
        logging.basicConfig(
            level=settings.log_level,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
        speak("Caul is ready. Say hello, or say goodbye to stop.")
        while True:
            command = listen(settings)
            if command is not None and not respond(
                command, listener=lambda: listen(settings)
            ):
                break
    except KeyboardInterrupt:
        speak("Goodbye!")
    except (OSError, ImportError, RuntimeError, ValueError) as error:
        logger.exception("Caul could not start or access its audio devices.")
        print("Caul audio/setup error:", error, file=sys.stderr)
        print(
            "Check the setup and microphone troubleshooting steps in README.md.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
