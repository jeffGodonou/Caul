"""Parse spoken event details and create calendar draft links."""

import re
import webbrowser
from datetime import datetime, timedelta
from urllib.parse import urlencode


CALENDARS = {
    "google": ("Google Calendar", "https://calendar.google.com/"),
    "outlook": ("Outlook Calendar", "https://outlook.live.com/calendar/0/view"),
}
CALENDAR_ALIASES = {
    "google": "google",
    "google calendar": "google",
    "outlook": "outlook",
    "outlook calendar": "outlook",
    "microsoft": "outlook",
}

_NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30,
    "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90,
}
_ORDINAL_WORDS = {
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
    "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
    "eleventh": 11, "twelfth": 12, "thirteenth": 13, "fourteenth": 14,
    "fifteenth": 15, "sixteenth": 16, "seventeenth": 17,
    "eighteenth": 18, "nineteenth": 19, "twentieth": 20,
    "thirtieth": 30,
}


def _spoken_number(text):
    words = text.replace("-", " ").split()
    if not words:
        return None
    if len(words) == 1 and words[0].isdigit():
        return int(words[0])
    numbers = {**_NUMBER_WORDS, **_ORDINAL_WORDS}
    if any(word not in numbers for word in words):
        return None
    if len(words) == 1:
        return numbers[words[0]]
    if len(words) == 2 and words[0] in {
        "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"
    } and numbers[words[1]] < 10:
        return numbers[words[0]] + numbers[words[1]]
    return None


def _calendar_date(text, now):
    text = text.strip().lower()
    if text in {"today", "tomorrow"}:
        return now.date() + timedelta(days=int(text == "tomorrow"))
    text = re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", text)
    words = text.replace(",", "").split()
    for index in range(2, len(words)):
        year_words = words[index:]
        if year_words[:1] == ["twenty"]:
            suffix = _spoken_number(" ".join(year_words[1:]))
        elif year_words[:2] == ["two", "thousand"]:
            suffix = _spoken_number(" ".join(year_words[2:]))
        else:
            continue
        if suffix is not None and 0 <= suffix <= 99:
            # Normalize spoken years like "twenty twenty six" to 2026.
            text = " ".join(words[:index]) + " " + str(2000 + suffix)
            break
    spoken = re.fullmatch(r"([a-z]+)\s+(.+?)\s+(\d{4})", text.replace(",", ""))
    if spoken:
        day = _spoken_number(spoken.group(2))
        if day is not None:
            text = f"{spoken.group(1)} {day} {spoken.group(3)}"
    for form in ("%Y-%m-%d", "%B %d %Y", "%b %d %Y"):
        try:
            return datetime.strptime(text.replace(",", ""), form).date()
        except ValueError:
            continue
    return None


def _calendar_time(text):
    """Parse a spoken or numeric time; bare hours stay ambiguous without AM/PM."""
    text = re.sub(r"\s+", " ", text.strip().lower().replace(".", ""))
    text = re.sub(r"\b([ap])\s+m\b", r"\1m", text)
    match = re.fullmatch(r"(.+?)\s*(am|pm)?", text)
    if not match:
        return None
    value, meridiem = match.groups()
    parts = value.strip().split()
    if len(parts) == 2 and parts[0] in _NUMBER_WORDS and parts[1] in _NUMBER_WORDS:
        hour, minute = _NUMBER_WORDS[parts[0]], _NUMBER_WORDS[parts[1]]
    elif value.strip() in _NUMBER_WORDS:
        hour, minute = _NUMBER_WORDS[value.strip()], 0
    else:
        numeric = re.fullmatch(r"(\d{1,2})(?::(\d{2}))?", value.strip())
        if not numeric:
            return None
        hour, minute = int(numeric.group(1)), int(numeric.group(2) or 0)
    if minute > 59:
        return None
    if meridiem:
        if not 1 <= hour <= 12:
            return None
        hour = hour % 12 + (12 if meridiem == "pm" else 0)
    elif not 13 <= hour <= 23 and hour != 0:
        # A value like "4" could mean morning or afternoon, so ask the user.
        return None
    return datetime.min.replace(hour=hour, minute=minute).time()


def _calendar_request(command):
    match = re.match(
        r"^(?:set (?:up )?(?:a )?|schedule (?:a )?|create (?:an? )?)"
        r"(?P<kind>meeting|event)\b\s*",
        command, re.IGNORECASE,
    )
    if match:
        title = command[match.end():].strip()
        if match.group("kind").lower() == "meeting":
            title = "Meeting " + title
    elif re.match(r"^session\b", command, re.IGNORECASE):
        title = command.strip()
    else:
        return None

    start_text = end_text = date_text = None
    time_part = re.search(r"\s+(?:from|at)\s+(.+)$", title, re.IGNORECASE)
    if time_part:
        title, time_text = title[:time_part.start()].strip(), time_part.group(1).strip()
        interval = re.fullmatch(r"(.+?)\s+(?:to|until)\s+(.+)", time_text, re.IGNORECASE)
        if interval:
            start_text, end_text = interval.groups()
        else:
            start_text = time_text
    date_part = re.search(r"(?:^|\s+)(?:for|on)\s+(.+)$", title, re.IGNORECASE)
    if date_part:
        title, date_text = title[:date_part.start()].strip(), date_part.group(1).strip()
    else:
        date_part = re.search(r"\s+(today|tomorrow)$", title, re.IGNORECASE)
        if date_part:
            title, date_text = title[:date_part.start()].strip(), date_part.group(1)
    return title.strip(), date_text, start_text, end_text


def _event_url(service, title, start, end):
    if service == "google":
        return "https://calendar.google.com/calendar/render?" + urlencode({
            "action": "TEMPLATE",
            "text": title,
            "dates": start.strftime("%Y%m%dT%H%M%S") + "/" + end.strftime("%Y%m%dT%H%M%S"),
        })
    return "https://outlook.live.com/calendar/deeplink/compose?" + urlencode({
        "path": "/calendar/action/compose",
        "rru": "addevent",
        "subject": title,
        "startdt": start.isoformat(timespec="seconds"),
        "enddt": end.isoformat(timespec="seconds"),
    })


def _prepare_calendar_event(request, speaker, listener, browser, now):
    title, date_text, start_text, end_text = request

    def ask(prompt, parse):
        while True:
            speaker(prompt)
            answer = listener()
            if not answer or not answer.strip():
                speaker("I didn't receive an answer. Event creation cancelled.")
                return None, True
            answer = answer.strip()
            if answer.lower() in {"quit", "exit", "goodbye"}:
                speaker("Goodbye!")
                return None, False
            if answer.lower() == "cancel":
                speaker("Event creation cancelled.")
                return None, True
            result = parse(answer)
            if result is not None:
                return result, True
            speaker("I couldn't understand that answer. Please try again or say cancel.")

    if not title:
        title, keep_going = ask("What is the event title?", lambda value: value)
        if title is None:
            return keep_going
    event_date = _calendar_date(date_text, now) if date_text else None
    if event_date is None:
        if date_text:
            speaker("I couldn't understand the event date.")
        event_date, keep_going = ask(
            "What date? Say today, tomorrow, or a date with the year.",
            lambda value: _calendar_date(value, now),
        )
        if event_date is None:
            return keep_going

    def get_time(value, prompt):
        parsed = _calendar_time(value) if value else None
        if parsed is not None:
            return parsed, True
        if value:
            speaker("I couldn't understand the time or it needs AM or PM.")
        return ask(prompt, _calendar_time)

    start_time, keep_going = get_time(start_text, "What time does it start? Include AM or PM.")
    if start_time is None:
        return keep_going
    while True:
        end_time, keep_going = get_time(end_text, "What time does it end? Include AM or PM.")
        if end_time is None:
            return keep_going
        # Event drafts currently support same-day events only.
        if end_time > start_time:
            break
        speaker("The end time must be after the start time on the same day.")
        end_text = None

    service, keep_going = ask(
        "Which calendar: Google or Outlook?",
        lambda value: CALENDAR_ALIASES.get(value.lower()),
    )
    if service is None:
        return keep_going
    start = datetime.combine(event_date, start_time)
    end = datetime.combine(event_date, end_time)
    label = CALENDARS[service][0]
    open_url = browser if browser is not None else webbrowser.open
    if open_url(_event_url(service, title, start, end)) is False:
        speaker("I couldn't open " + label + ". Please check your browser.")
        return True
    speaker("Opening an event draft in " + label + ". Review the date, time and time zone, then save it.")
    return True
