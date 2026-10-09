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
            "I can greet you, tell you the time, search Google or YouTube, check the weather, play music, open Calculator, Notepad, Google, or YouTube, or stop when you say goodbye."
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

    def test_google_search_encodes_spaces_and_punctuation(self):
        browser = Mock()
        self.assertTrue(
            respond("search for C++ & cats?", speaker=self.speaker, browser=browser)
        )
        browser.assert_called_once_with(
            "https://www.google.com/search?q=C%2B%2B+%26+cats%3F"
        )
        self.speaker.assert_called_once_with("Searching Google for C++ & cats?.")

    def test_youtube_search_encodes_spaces_and_punctuation(self):
        browser = Mock()
        self.assertTrue(
            respond("search YouTube for lo-fi & jazz!", speaker=self.speaker, browser=browser)
        )
        browser.assert_called_once_with(
            "https://www.youtube.com/results?search_query=lo-fi+%26+jazz%21"
        )
        self.speaker.assert_called_once_with("Searching YouTube for lo-fi & jazz!.")

    def test_search_without_query_does_not_open_browser(self):
        browser = Mock()
        self.assertTrue(respond("search for", speaker=self.speaker, browser=browser))
        browser.assert_not_called()
        self.speaker.assert_called_once_with("Tell me what you'd like me to search for.")

    def test_empty_phrase_keeps_listening(self):
        self.assertTrue(respond(None, speaker=self.speaker))
        self.speaker.assert_not_called()

    def test_goodbye_stops_the_loop(self):
        self.assertFalse(respond("goodbye", speaker=self.speaker))
        self.speaker.assert_called_once_with("Goodbye!")

    def test_open_calculator_runs_allowlisted_app(self):
        launcher = Mock()
        self.assertTrue(respond("open calculator", speaker=self.speaker, app_launcher=launcher))
        launcher.assert_called_once_with(["calc.exe"])
        self.speaker.assert_called_once_with("Opening Calculator.")

    def test_open_google_opens_allowlisted_website(self):
        browser = Mock()
        self.assertTrue(respond("open google", speaker=self.speaker, browser=browser))
        browser.assert_called_once_with("https://www.google.com/")
        self.speaker.assert_called_once_with("Opening Google.")

    def test_open_youtube_opens_allowlisted_website(self):
        browser = Mock()
        self.assertTrue(respond("open youtube", speaker=self.speaker, browser=browser))
        browser.assert_called_once_with("https://www.youtube.com/")
        self.speaker.assert_called_once_with("Opening YouTube.")

    def test_open_notepad_runs_allowlisted_app(self):
        launcher = Mock()
        self.assertTrue(respond("open notepad", speaker=self.speaker, app_launcher=launcher))
        launcher.assert_called_once_with(["notepad.exe"])
        self.speaker.assert_called_once_with("Opening Notepad.")

    def test_open_unknown_target_is_refused(self):
        browser = Mock()
        launcher = Mock()
        self.assertTrue(
            respond("open chrome", speaker=self.speaker, browser=browser, app_launcher=launcher)
        )
        browser.assert_not_called()
        launcher.assert_not_called()
        self.speaker.assert_called_once_with(
            "I can only open Calculator, Notepad, Google, or YouTube."
        )

    def test_weather_in_location_searches_google_weather(self):
        browser = Mock()
        self.assertTrue(
            respond("what's the weather in Paris", speaker=self.speaker, browser=browser)
        )
        browser.assert_called_once_with(
            "https://www.google.com/search?q=weather+Paris"
        )
        self.speaker.assert_called_once_with("Checking the weather in Paris.")

    def test_weather_without_location_asks_for_location(self):
        browser = Mock()
        self.assertTrue(respond("weather", speaker=self.speaker, browser=browser))
        browser.assert_not_called()
        self.speaker.assert_called_once_with(
            "Tell me which location you want the weather for."
        )

    def test_play_song_opens_spotify_search_with_punctuation(self):
        browser = Mock()
        self.assertTrue(
            respond("play lo-fi & jazz!", speaker=self.speaker, browser=browser)
        )
        browser.assert_called_once_with(
            "https://open.spotify.com/search/lo-fi%20%26%20jazz%21"
        )
        self.speaker.assert_called_once_with("Playing lo-fi & jazz! on Spotify.")


if __name__ == "__main__":
    unittest.main()
