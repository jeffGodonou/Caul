import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np

from caul import main, respond
from caul_audio import _record
from caul_alerts import AlertManager, _timer_seconds
from caul_settings import Settings


class AlertManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.temp_dir.name, "alerts.json")
        self.now = datetime(2026, 11, 18, 17, 0).astimezone()
        self.speaker = Mock()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_alert_and_timer_persist_and_fire_once_after_reload(self):
        manager = AlertManager(self.speaker, self.path)
        manager.schedule_alert(self.now + timedelta(minutes=1), self.now)
        manager.schedule_timer(120, self.now)

        restarted = AlertManager(self.speaker, self.path)
        self.assertFalse(restarted.check_due(self.now))
        self.assertTrue(restarted.check_due(self.now + timedelta(minutes=1)))
        self.assertEqual(self.speaker.call_args.args[0], "Your alert is due.")
        self.assertTrue(restarted.check_due(self.now + timedelta(minutes=2)))
        self.assertEqual(self.speaker.call_args.args[0], "Your timer is finished.")
        self.assertFalse(restarted.check_due(self.now + timedelta(minutes=3)))

    def test_overdue_alert_is_announced_when_caul_starts(self):
        due_at = (datetime.now().astimezone() - timedelta(minutes=1)).isoformat()
        with open(self.path, "w", encoding="utf-8") as alert_file:
            json.dump([{"id": "missed", "kind": "alert", "due_at": due_at}], alert_file)
        manager = AlertManager(self.speaker, self.path)

        with unittest.mock.patch("caul.listen", return_value="goodbye"), unittest.mock.patch(
            "caul.respond", return_value=False
        ), unittest.mock.patch("caul.speak"):
            main(Settings(), alert_manager=manager)

        self.speaker.assert_called_once_with("Your alert is due.")

    def test_alert_for_future_time_today_is_saved(self):
        manager = AlertManager(self.speaker, self.path)
        self.assertTrue(respond(
            "set an alert for 6 PM",
            speaker=self.speaker,
            clock=lambda: self.now,
            alert_manager=manager,
        ))
        self.assertEqual(len(manager._items), 1)
        due_at = datetime.fromisoformat(manager._items[0]["due_at"])
        self.assertEqual((due_at.date(), due_at.hour), (self.now.date(), 18))
        self.assertIn("Alert set for", self.speaker.call_args.args[0])

    def test_alert_for_past_time_asks_for_future_date(self):
        manager = AlertManager(self.speaker, self.path)
        listener = Mock(return_value="tomorrow")
        self.assertTrue(respond(
            "set an alert for 4 PM",
            speaker=self.speaker,
            listener=listener,
            clock=lambda: self.now,
            alert_manager=manager,
        ))
        due_at = datetime.fromisoformat(manager._items[0]["due_at"])
        self.assertEqual(due_at.date(), (self.now + timedelta(days=1)).date())
        listener.assert_called_once()

    def test_alert_accepts_date_before_time(self):
        manager = AlertManager(self.speaker, self.path)
        self.assertTrue(respond(
            "set an alert for tomorrow at 6 PM",
            speaker=self.speaker,
            clock=lambda: self.now,
            alert_manager=manager,
        ))
        due_at = datetime.fromisoformat(manager._items[0]["due_at"])
        self.assertEqual((due_at.date(), due_at.hour), (
            (self.now + timedelta(days=1)).date(), 18
        ))

    def test_alert_reprompts_for_an_unrecognized_date(self):
        manager = AlertManager(self.speaker, self.path)
        listener = Mock(return_value="tomorrow")
        self.assertTrue(respond(
            "set an alert for 6 PM on not-a-date",
            speaker=self.speaker,
            listener=listener,
            clock=lambda: self.now,
            alert_manager=manager,
        ))
        due_at = datetime.fromisoformat(manager._items[0]["due_at"])
        self.assertEqual(due_at.date(), (self.now + timedelta(days=1)).date())
        listener.assert_called_once()

    def test_timer_command_saves_requested_duration(self):
        manager = AlertManager(self.speaker, self.path)
        self.assertTrue(respond(
            "start a timer for 10 minutes",
            speaker=self.speaker,
            clock=lambda: self.now,
            alert_manager=manager,
        ))
        due_at = datetime.fromisoformat(manager._items[0]["due_at"])
        self.assertEqual(due_at, self.now + timedelta(minutes=10))
        self.speaker.assert_called_once_with("Timer started for 10 minutes.")

    def test_missing_timer_duration_is_prompted_and_can_be_cancelled(self):
        manager = AlertManager(self.speaker, self.path)
        listener = Mock(return_value="cancel")
        self.assertTrue(respond(
            "start a timer",
            speaker=self.speaker,
            listener=listener,
            clock=lambda: self.now,
            alert_manager=manager,
        ))
        listener.assert_called_once()
        self.assertEqual(manager._items, [])

    def test_duration_parser_accepts_words_and_rejects_invalid_values(self):
        self.assertEqual(_timer_seconds("one hour and thirty minutes"), 5400)
        self.assertEqual(_timer_seconds("2 minutes 5 seconds"), 125)
        self.assertIsNone(_timer_seconds("several minutes"))
        self.assertIsNone(_timer_seconds("0 seconds"))

    def test_invalid_saved_alert_data_is_reported(self):
        with open(self.path, "w", encoding="utf-8") as alert_file:
            json.dump({"not": "a list"}, alert_file)
        with self.assertRaisesRegex(RuntimeError, "Could not read saved alerts"):
            AlertManager(self.speaker, self.path)

    def test_due_alert_stops_listening_before_its_speech_is_recorded(self):
        class FakeStream:
            reads = 0

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, frames):
                self.reads += 1
                return np.zeros((frames, 1), dtype=np.int16), None

        stream = FakeStream()
        sounddevice = SimpleNamespace(
            PortAudioError=type("PortAudioError", (Exception,), {}),
            InputStream=Mock(return_value=stream),
        )
        on_wait = Mock(return_value=True)
        with unittest.mock.patch.dict("sys.modules", {"sounddevice": sounddevice}):
            self.assertIsNone(_record(Settings(), on_wait=on_wait))
        on_wait.assert_called_once_with()
        self.assertEqual(stream.reads, 1)


if __name__ == "__main__":
    unittest.main()
