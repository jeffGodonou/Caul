import unittest
from datetime import datetime
from unittest.mock import Mock

from caul import respond


class StarterCommandTests(unittest.TestCase):
    def setUp(self):
        self.speaker = Mock()

    def test_greeting_gets_a_response(self):
        self.assertTrue(respond("hello", speaker=self.speaker))
        self.speaker.assert_called_once()
        self.assertIn("Hello", self.speaker.call_args.args[0])

    def test_unknown_phrase_gets_helpful_response(self):
        self.assertTrue(respond("test phrase", speaker=self.speaker))
        self.speaker.assert_called_once_with(
            "I don't know that command. Say help to hear what I can do."
        )

    def test_help_command_lists_supported_actions(self):
        self.assertTrue(respond("help", speaker=self.speaker))
        self.speaker.assert_called_once_with(
            "I can greet you, tell you the current time, or stop when you say goodbye."
        )

    def test_time_command_speaks_the_current_time(self):
        clock = Mock(return_value=datetime(2026, 10, 2, 9, 5))
        self.assertTrue(respond("what time is it", speaker=self.speaker, clock=clock))
        clock.assert_called_once_with()
        self.speaker.assert_called_once_with("The current time is 9:05 AM.")

    def test_hi_inside_a_sentence_does_not_trigger_greeting(self):
        self.assertTrue(respond("this is a sentence", speaker=self.speaker))
        self.speaker.assert_called_once_with(
            "I don't know that command. Say help to hear what I can do."
        )

    def test_empty_phrase_keeps_listening(self):
        self.assertTrue(respond(None, speaker=self.speaker))
        self.speaker.assert_not_called()

    def test_goodbye_stops_the_loop(self):
        self.assertFalse(respond("goodbye", speaker=self.speaker))
        self.speaker.assert_called_once_with("Goodbye!")


if __name__ == "__main__":
    unittest.main()
