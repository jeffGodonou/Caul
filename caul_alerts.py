"""Persist one-shot alerts and timers and announce them when they become due."""

import json
import logging
import os
import re
import tempfile
import uuid
from datetime import datetime, timedelta, timezone

from caul_calendar import _calendar_date, _calendar_time, _spoken_number


logger = logging.getLogger("caul")


def _default_alert_path():
    data_root = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(data_root, "Caul", "alerts.json")


def _as_utc(value):
    if value.tzinfo is None:
        value = value.astimezone()
    return value.astimezone(timezone.utc)


def _as_local(value):
    return value.astimezone() if value.tzinfo is None else value


class AlertManager:
    """Keep scheduled deadlines on disk and notify once when each is due."""

    def __init__(self, speaker, path=None):
        self.speaker = speaker
        self.path = path or _default_alert_path()
        self._items = self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return []
        try:
            with open(self.path, encoding="utf-8") as alert_file:
                items = json.load(alert_file)
            if not isinstance(items, list):
                raise ValueError("the alert data must be a list")
            for item in items:
                if (
                    not isinstance(item, dict)
                    or not isinstance(item.get("id"), str)
                    or item.get("kind") not in {"alert", "timer"}
                    or not isinstance(item.get("due_at"), str)
                ):
                    raise ValueError("an alert entry has invalid fields")
                datetime.fromisoformat(item["due_at"])
            return items
        except (OSError, ValueError, KeyError) as error:
            raise RuntimeError("Could not read saved alerts at " + self.path) from error

    def _save(self):
        directory = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(directory, exist_ok=True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=directory, delete=False
            ) as alert_file:
                temporary_path = alert_file.name
                json.dump(self._items, alert_file, indent=2)
                alert_file.write("\n")
                alert_file.flush()
                os.fsync(alert_file.fileno())
            os.replace(temporary_path, self.path)
        except OSError:
            if temporary_path and os.path.exists(temporary_path):
                os.remove(temporary_path)
            raise

    def _schedule(self, kind, due_at, now=None):
        if _as_utc(due_at) <= _as_utc(now or datetime.now().astimezone()):
            raise ValueError("The scheduled time must be in the future.")
        item = {
            "id": uuid.uuid4().hex,
            "kind": kind,
            "due_at": _as_local(due_at).isoformat(),
        }
        self._items.append(item)
        try:
            self._save()
        except OSError:
            self._items.pop()
            raise

    def schedule_alert(self, due_at, now=None):
        self._schedule("alert", due_at, now)

    def schedule_timer(self, seconds, now=None):
        if seconds <= 0:
            raise ValueError("A timer duration must be positive.")
        started_at = now or datetime.now().astimezone()
        self._schedule("timer", started_at + timedelta(seconds=seconds), started_at)

    def check_due(self, now=None):
        """Speak due items once; return whether an announcement interrupted listening."""
        current_time = _as_utc(now or datetime.now().astimezone())
        due = [
            item for item in self._items
            if _as_utc(datetime.fromisoformat(item["due_at"])) <= current_time
        ]
        if not due:
            return False

        due_ids = {item["id"] for item in due}
        remaining = [item for item in self._items if item["id"] not in due_ids]
        previous_items = self._items
        self._items = remaining
        try:
            self._save()
        except OSError:
            self._items = previous_items
            raise

        for item in due:
            message = "Your alert is due." if item["kind"] == "alert" else "Your timer is finished."
            self.speaker(message)
        return True


def _alert_request(command):
    match = re.fullmatch(
        r"(?:set (?:an? )?alert(?:\s+(?:for|at))?|alert me (?:for|at))\s*(.*)",
        command.strip(),
        re.IGNORECASE,
    )
    if match:
        return "alert", match.group(1).strip()

    match = re.fullmatch(
        r"(?:(?:start|set) (?:a )?timer(?: for)?|timer(?: for)?)\s*(.*)",
        command.strip(),
        re.IGNORECASE,
    )
    if match:
        return "timer", match.group(1).strip()
    return None


_DURATION_PART = re.compile(
    r"(?P<amount>\d+|[a-z]+(?:[\s-]+[a-z]+)?)\s*"
    r"(?P<unit>hours?|hrs?|minutes?|mins?|seconds?|secs?)\b",
    re.IGNORECASE,
)


def _timer_seconds(text):
    text = re.sub(r"\band\b|,", " ", text.lower())
    seconds = 0
    position = 0
    matches = list(_DURATION_PART.finditer(text))
    if not matches:
        return None
    for match in matches:
        if text[position:match.start()].strip():
            return None
        amount_text = match.group("amount")
        amount = int(amount_text) if amount_text.isdigit() else _spoken_number(amount_text)
        if amount is None:
            return None
        unit = match.group("unit")
        multiplier = (
            3600 if unit.startswith(("hour", "hr"))
            else 60 if unit.startswith(("minute", "min"))
            else 1
        )
        seconds += amount * multiplier
        position = match.end()
    if text[position:].strip() or seconds <= 0:
        return None
    return seconds


def _alert_time_and_date(text, now):
    text = text.strip()
    date_text = None
    match = re.fullmatch(r"(today|tomorrow)\s+(?:at\s+)?(.+)", text, re.IGNORECASE)
    if match:
        date_text, text = match.groups()
    else:
        match = re.fullmatch(r"(.+?)\s+(?:on|for)\s+(.+)", text, re.IGNORECASE)
        if match:
            text, date_text = match.groups()
        else:
            match = re.fullmatch(r"(.+?)\s+(today|tomorrow)", text, re.IGNORECASE)
            if match:
                text, date_text = match.groups()

    parsed_time = _calendar_time(text)
    parsed_date = _calendar_date(date_text, now) if date_text else now.date()
    if parsed_time is None or parsed_date is None:
        return None, parsed_date, parsed_time, date_text is not None
    target = datetime.combine(parsed_date, parsed_time).astimezone()
    return target, parsed_date, parsed_time, date_text is not None


def _format_duration(seconds):
    parts = []
    for unit_seconds, unit_name in ((3600, "hour"), (60, "minute"), (1, "second")):
        amount, seconds = divmod(seconds, unit_seconds)
        if amount:
            parts.append(str(amount) + " " + unit_name + ("s" if amount != 1 else ""))
    return " ".join(parts)


def handle_alert_request(request, manager, speaker, listener, now=None):
    """Prompt for missing details, then persist an alert or timer."""
    kind, value = request
    current_time = now or datetime.now().astimezone()

    def ask(prompt, parse):
        while True:
            speaker(prompt)
            answer = listener()
            if not answer or not answer.strip():
                speaker("I didn't receive an answer. Cancelled.")
                return None, True
            answer = answer.strip()
            if answer.lower() == "cancel":
                speaker("Cancelled.")
                return None, True
            if answer.lower() in {"quit", "exit", "goodbye"}:
                speaker("Goodbye!")
                return None, False
            result = parse(answer)
            if result is not None:
                return result, True
            speaker("I couldn't understand that. Please try again or say cancel.")

    if kind == "timer":
        seconds = _timer_seconds(value) if value else None
        if seconds is None:
            seconds, keep_going = ask(
                "How long should the timer run? Say a duration such as 10 minutes.",
                _timer_seconds,
            )
            if seconds is None:
                return keep_going
        try:
            manager.schedule_timer(seconds, current_time)
        except (OSError, OverflowError, ValueError):
            logger.exception("Could not save timer.")
            speaker("I couldn't save the timer. Please check the available storage.")
            return True
        speaker("Timer started for " + _format_duration(seconds) + ".")
        return True

    if value:
        target, parsed_date, parsed_time, has_date = _alert_time_and_date(value, current_time)
    else:
        target, parsed_date, parsed_time, has_date = None, None, None, False

    if parsed_time is None:
        if value:
            speaker("I couldn't understand the time. Please include AM or PM.")
        parsed_time, keep_going = ask(
            "What time should I alert you? Please include AM or PM.",
            _calendar_time,
        )
        if parsed_time is None:
            return keep_going

    if has_date and parsed_date is None:
        speaker("I couldn't understand the date.")
        parsed_date, keep_going = ask(
            "What date should I set it for? Say today, tomorrow or a date with the year.",
            lambda answer: _calendar_date(answer, current_time),
        )
        if parsed_date is None:
            return keep_going

    if target is None:
        event_date = parsed_date or _as_local(current_time).date()
        target = datetime.combine(event_date, parsed_time).astimezone()

    while _as_utc(target) <= _as_utc(current_time):
        speaker("That time has already passed.")
        date_text, keep_going = ask(
            "What date should I set it for? Say tomorrow or a date with the year.",
            lambda answer: _calendar_date(answer, current_time),
        )
        if date_text is None:
            return keep_going
        target = datetime.combine(date_text, target.time()).astimezone()

    try:
        manager.schedule_alert(target, current_time)
    except (OSError, OverflowError, ValueError):
        logger.exception("Could not save alert.")
        speaker("I couldn't save the alert. Please check the available storage.")
        return True
    speaker("Alert set for " + target.strftime("%B %d at %I:%M %p").lstrip("0") + ".")
    return True
