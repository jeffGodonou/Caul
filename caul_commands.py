"""Route recognized phrases to Caul's supported actions."""

import logging
import os
import random
import subprocess
import tempfile
import webbrowser
from datetime import datetime
from urllib.parse import quote, urlencode

from caul_alerts import AlertManager, _alert_request, handle_alert_request
from caul_calendar import (
    CALENDARS,
    CALENDAR_ALIASES,
    _calendar_request,
    _prepare_calendar_event,
)
from caul_math import _format_number, calculate


logger = logging.getLogger("caul")


def respond(
    command,
    speaker,
    clock=None,
    browser=None,
    app_launcher=None,
    random_choice=random.choice,
    listener=None,
    calculate_function=calculate,
    format_number=_format_number,
    calendar_request=_calendar_request,
    prepare_event=_prepare_calendar_event,
    calendars=CALENDARS,
    calendar_aliases=CALENDAR_ALIASES,
    alert_manager=None,
):
    """Handle supported commands and return False when asked to exit."""
    command = (command or "").strip()
    normalized = command.lower()

    # Handle exact short phrases before prefix-based command matching.
    if normalized in {"quit", "exit", "goodbye"}:
        speaker("Goodbye! See you soon...")
        return False
    if normalized in {"hello", "hi", "hey"}:
        speaker("Hello! I'm Caul. Say goodbye when you want me to stop.")
        return True
    if normalized in {"help", "what can you do"}:
        speaker("I can greet you, tell you the time, calculate basic arithmetic, " \
        "play rock-paper-scissors, search Google or YouTube, check the weather, " \
        "play music, set alerts and timers, create notes and documents, prepare calendar events, " \
        "open Google or Outlook Calendar, Calculator, Notepad, Google, or YouTube, or stop when you say goodbye.")
        return True
    if normalized in {"time", "what time is it"}:
        current_time = (clock or datetime.now)().strftime("%I:%M %p").lstrip("0")
        speaker("The current time is " + current_time + ".")
        return True
    if normalized in {"weather", "what's the weather", "what is the weather"}:
        speaker("Tell me which location you want the weather for.")
        return True
    if normalized in {
        "search for",
        "google search for",
        "search youtube for",
        "youtube search for",
    }:
        speaker("Tell me what you'd like me to search for.")
        return True

    if normalized in {"create a note", "create note", "make a note", "take a note"}:
        speaker("What would you like the note to say? Say cancel to stop.")
        note = listener()
        if not note or not note.strip():
            speaker("I didn't receive a note. Note creation cancelled.")
            return True
        note = note.strip()
        if note.lower() == "cancel":
            speaker("Note creation cancelled.")
            return True
        if note.lower() in {"quit", "exit", "goodbye"}:
            speaker("Goodbye!")
            return False
        note_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", prefix="caul-note-", suffix=".txt",
                delete=False,
            ) as note_file:
                note_path = note_file.name
                note_file.write(note)
        except OSError:
            logger.exception("Could not write temporary note.")
            if note_path is not None:
                try:
                    os.remove(note_path)
                except OSError:
                    logger.exception("Could not remove incomplete temporary note.")
            speaker("I couldn't write the note. Please check the available storage.")
            return True
        launch = app_launcher if app_launcher is not None else subprocess.Popen
        try:
            launch(["notepad.exe", note_path])
        except OSError:
            logger.exception("Could not open the temporary note in Notepad.")
            speaker("I couldn't open Notepad. Your temporary note is at " + note_path + ".")
            return True
        speaker("Opening your temporary note in Notepad. Use Save As to keep it.")
        return True

    if normalized in {"start a document", "start document", "create a document", "create document"}:
        launch = app_launcher if app_launcher is not None else subprocess.Popen
        try:
            launch(["notepad.exe"])
        except OSError:
            logger.exception("Could not open a document in Notepad.")
            speaker("I couldn't open Notepad. Please check that it is installed.")
            return True
        speaker("Opening a blank document in Notepad.")
        return True

    alert_request = _alert_request(command)
    if alert_request is not None:
        if alert_manager is None:
            alert_manager = AlertManager(speaker)
        return handle_alert_request(
            alert_request,
            alert_manager,
            speaker,
            listener,
            (clock or datetime.now)(),
        )

    # Calendar phrases overlap with ordinary wording, so recognize them first.
    event_request = calendar_request(command)
    if event_request is not None:
        return prepare_event(
            event_request, speaker, listener, browser, (clock or datetime.now)(),
        )

    calculation = command
    for prefix in ("calculate ", "what is ", "what's "):
        if normalized.startswith(prefix):
            calculation = command[len(prefix):].strip()
            break
    is_weather_request = normalized.startswith(
        ("what's the weather", "what is the weather")
    )
    if not is_weather_request and (
        calculation != command or normalized.startswith(("calculate", "what is", "what's"))
    ):
        if not calculation:
            speaker("Tell me what you'd like me to calculate.")
            return True
        try:
            result = calculate_function(calculation)
        except (SyntaxError, ValueError, TypeError, ZeroDivisionError):
            speaker("I can only calculate basic arithmetic, such as 2 plus 2.")
            return True
        speaker("The answer is " + format_number(result) + ".")
        return True

    if normalized.startswith("rock paper scissors"):
        move = normalized[len("rock paper scissors"):].strip()
        if not move:
            speaker("Choose rock, paper, or scissors.")
            return True
        if move not in {"rock", "paper", "scissors"}:
            speaker("That is not a valid move. Choose rock, paper, or scissors.")
            return True
        computer_move = random_choice(["rock", "paper", "scissors"])
        if move == computer_move:
            outcome = "It's a tie."
        elif (move, computer_move) in {
            ("rock", "scissors"),
            ("paper", "rock"),
            ("scissors", "paper"),
        }:
            outcome = "You win!"
        else:
            outcome = "I win!"
        speaker("You chose " + move + ". I chose " + computer_move + ". " + outcome)
        return True
    search_prefixes = (
        ("search youtube for ", "youtube"),
        ("youtube search for ", "youtube"),
        ("google search for ", "google"),
        ("search for ", "google"),
    )
    for prefix, service in search_prefixes:
        if normalized.startswith(prefix):
            query = command[len(prefix):].strip()
            if not query:
                speaker("Tell me what you'd like me to search for.")
                return True
            if service == "youtube":
                url = "https://www.youtube.com/results?" + urlencode({"search_query": query})
            else:
                url = "https://www.google.com/search?" + urlencode({"q": query})
            open_url = browser if browser is not None else webbrowser.open
            open_url(url)
            service_name = "YouTube" if service == "youtube" else "Google"
            speaker("Searching " + service_name + " for " + query + ".")
            return True

    weather_prefixes = (
        "weather in ",
        "what's the weather in ",
        "what is the weather in ",
    )
    for prefix in weather_prefixes:
        if normalized.startswith(prefix):
            location = command[len(prefix):].strip()
            if not location:
                speaker("Tell me which location you want the weather for.")
                return True
            open_url = browser if browser is not None else webbrowser.open
            open_url("https://www.google.com/search?" + urlencode({"q": "weather " + location}))
            speaker("Checking the weather in " + location + ".")
            return True

    if normalized.startswith("play "):
        song = command[len("play "):].strip()
        if not song:
            speaker("What song would you like me to play?")
            return True
        open_url = browser if browser is not None else webbrowser.open
        open_url("https://open.spotify.com/search/" + quote(song, safe=""))
        speaker("Playing " + song + " on Spotify.")
        return True

    if normalized == "open calendar":
        speaker("Which calendar would you like to open: Google or Outlook?")
        choice = listener()
        if not choice or not choice.strip():
            speaker("No calendar selected. Say open calendar to try again.")
            return True
        choice = choice.strip().lower()
        if choice in {"quit", "exit", "goodbye"}:
            speaker("Goodbye!")
            return False
        if choice == "cancel":
            speaker("Calendar opening cancelled.")
            return True
        service = calendar_aliases.get(choice)
        if service is None:
            speaker("I can open Google or Outlook Calendar. Say open calendar to try again.")
            return True
        label, url = calendars[service]
        open_url = browser if browser is not None else webbrowser.open
        if open_url(url) is False:
            speaker("I couldn't open " + label + ". Please check your browser.")
            return True
        speaker("Opening " + label + ".")
        return True

    if normalized.startswith("open "):
        target = normalized[len("open "):].strip()
        # Explicit allowlists prevent spoken text from becoming an arbitrary launch.
        apps = {
            "calculator": ["calc.exe"],
            "notepad": ["notepad.exe"],
        }
        websites = {
            "google": "https://www.google.com/",
            "youtube": "https://www.youtube.com/",
        }
        labels = {
            "calculator": "Calculator",
            "notepad": "Notepad",
            "google": "Google",
            "youtube": "YouTube",
        }
        if target in apps:
            launch = app_launcher if app_launcher is not None else subprocess.Popen
            launch(apps[target])
            speaker("Opening " + labels[target] + ".")
            return True
        if target in websites:
            open_url = browser if browser is not None else webbrowser.open
            open_url(websites[target])
            speaker("Opening " + labels[target] + ".")
            return True
        speaker("I can only open Calculator, Notepad, Google, or YouTube.")
        return True
    if command:
        speaker("I don't know that command. Say help to hear what I can do.")
    return True
