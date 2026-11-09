import unittest
import logging
import os
from contextlib import redirect_stderr
from datetime import datetime
from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

from caul import (
    DEFAULT_VOSK_MODEL,
    MicrophoneError,
    Settings,
    _default_model_path,
    _recognize,
    _record,
    calculate,
    load_settings,
    listen,
    main,
    respond,
)


class StarterCommandTests(unittest.TestCase):
    def setUp(self):
        self.speaker = Mock()

    def test_settings_use_safe_defaults(self):
        self.assertEqual(load_settings({}), Settings())

    def test_settings_read_microphone_and_audio_options(self):
        settings = load_settings(
            {
                "CAUL_MICROPHONE_DEVICE": "2",
                "CAUL_LISTEN_TIMEOUT": "3.5",
                "CAUL_PHRASE_TIME_LIMIT": "6",
                "CAUL_SAMPLE_RATE": "22050",
                "CAUL_LOG_LEVEL": "INFO",
                "CAUL_VOSK_MODEL": "D:/models/vosk",
            }
        )
        self.assertEqual(
            settings,
            Settings(
                microphone_device=2,
                listen_timeout=3.5,
                phrase_time_limit=6,
                sample_rate=22050,
                log_level=logging.INFO,
                vosk_model="D:/models/vosk",
            ),
        )

    def test_settings_reject_invalid_values(self):
        for name, value in (
            ("CAUL_MICROPHONE_DEVICE", "default"),
            ("CAUL_MICROPHONE_DEVICE", "-1"),
            ("CAUL_LISTEN_TIMEOUT", "0"),
            ("CAUL_LISTEN_TIMEOUT", "nan"),
            ("CAUL_PHRASE_TIME_LIMIT", "inf"),
            ("CAUL_SAMPLE_RATE", "fast"),
            ("CAUL_LOG_LEVEL", "VERBOSE"),
        ):
            with self.subTest(name=name, value=value):
                with self.assertRaises(ValueError):
                    load_settings({name: value})

    def test_portaudio_device_errors_become_clear_microphone_errors(self):
        port_audio_error = type("PortAudioError", (Exception,), {})
        sounddevice = SimpleNamespace(
            PortAudioError=port_audio_error,
            InputStream=Mock(side_effect=port_audio_error("no input device")),
        )
        with patch.dict("sys.modules", {"numpy": Mock(), "sounddevice": sounddevice}):
            with self.assertRaisesRegex(MicrophoneError, "no input device"):
                _record(Settings())

    @patch("caul._recognize", return_value="hello")
    @patch("caul._record", return_value=b"pcm")
    def test_listen_returns_recognized_text(self, record, recognize):
        settings = Settings()
        self.assertEqual(listen(settings), "hello")
        record.assert_called_once_with(settings)
        recognize.assert_called_once_with(b"pcm", settings)

    @patch("caul.speak")
    @patch("caul._recognize", return_value="")
    @patch("caul._record", return_value=b"pcm")
    def test_listen_asks_for_retry_when_speech_is_unclear(
        self, record, recognize, speaker
    ):
        self.assertIsNone(listen(Settings()))
        speaker.assert_called_once_with("I didn't catch that. Please try again.")

    @patch("caul._recognize")
    @patch("caul._record", return_value=None)
    def test_listen_skips_recognition_when_nothing_is_heard(self, record, recognize):
        self.assertIsNone(listen(Settings()))
        recognize.assert_not_called()

    def test_recognize_without_model_explains_setup(self):
        with self.assertRaisesRegex(RuntimeError, "Vosk model not found"):
            _recognize(b"\0\0", Settings(vosk_model="no/such/model"))

    def test_default_model_path_prefers_models_folder_next_to_caul(self):
        import caul

        with patch("caul.os.path.isdir", return_value=True):
            path = _default_model_path()
        expected = os.path.join(
            os.path.dirname(os.path.abspath(caul.__file__)),
            "models",
            "vosk-model-small-en-us-0.15",
        )
        self.assertEqual(path, expected)

    def test_default_model_path_falls_back_to_user_data_folder(self):
        with patch("caul.os.path.isdir", return_value=False):
            path = _default_model_path()
        self.assertTrue(path.endswith("vosk-model-small-en-us-0.15"))
        self.assertIn(os.path.join("Caul", "models"), path)

    def test_default_model_path_is_a_valid_setting(self):
        self.assertTrue(DEFAULT_VOSK_MODEL.endswith("vosk-model-small-en-us-0.15"))

    @patch("caul.speak")
    @patch("caul.listen", side_effect=OSError("no input device"))
    def test_main_reports_microphone_failure_without_crashing(self, listen_once, speaker):
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertLogs("caul", level="ERROR"):
            main(Settings())
        self.assertIn("Caul audio/setup error: no input device", stderr.getvalue())
        speaker.assert_called_once_with("Caul is ready. Say hello, or say goodbye to stop.")

    @patch("caul.speak")
    @patch("caul.listen", side_effect=[None, "goodbye"])
    def test_main_keeps_listening_after_unclear_audio(self, listen_once, speaker):
        main(Settings())
        self.assertEqual(listen_once.call_count, 2)

    @patch("caul.speak")
    @patch("caul.listen", return_value="goodbye")
    def test_main_stops_listening_after_goodbye(self, listen_once, speaker):
        with patch(
            "caul.respond",
            side_effect=lambda command: respond(command, speaker=speaker),
        ):
            main(Settings())
        listen_once.assert_called_once_with(Settings())
        self.assertEqual(
            speaker.call_args_list,
            [
                unittest.mock.call(
                    "Caul is ready. Say hello, or say goodbye to stop."
                ),
                unittest.mock.call("Goodbye!"),
            ],
        )

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
            "I can greet you, tell you the time, calculate basic arithmetic, play rock-paper-scissors, search Google or YouTube, check the weather, play music, open Calculator, Notepad, Google, or YouTube, or stop when you say goodbye."
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

    def test_calculate_supports_basic_operations(self):
        self.assertEqual(calculate("2 plus 3 * 4"), 14)

    def test_calculate_command_speaks_result(self):
        self.assertTrue(respond("calculate 12 divided by 3", speaker=self.speaker))
        self.speaker.assert_called_once_with("The answer is 4.")

    def test_calculate_supports_decimal_results(self):
        self.assertTrue(respond("what is 5 minus 2.5", speaker=self.speaker))
        self.speaker.assert_called_once_with("The answer is 2.5.")

    def test_calculate_invalid_input_does_not_crash(self):
        self.assertTrue(respond("calculate launch missiles", speaker=self.speaker))
        self.speaker.assert_called_once_with(
            "I can only calculate basic arithmetic, such as 2 plus 2."
        )

    def test_calculate_division_by_zero_does_not_crash(self):
        self.assertTrue(respond("calculate 8 divided by 0", speaker=self.speaker))
        self.speaker.assert_called_once_with(
            "I can only calculate basic arithmetic, such as 2 plus 2."
        )

    def test_rock_paper_scissors_reports_win(self):
        random_choice = Mock(return_value="scissors")
        self.assertTrue(
            respond(
                "rock paper scissors rock",
                speaker=self.speaker,
                random_choice=random_choice,
            )
        )
        random_choice.assert_called_once_with(["rock", "paper", "scissors"])
        self.speaker.assert_called_once_with(
            "You chose rock. I chose scissors. You win!"
        )

    def test_rock_paper_scissors_reports_tie(self):
        self.assertTrue(
            respond(
                "rock paper scissors paper",
                speaker=self.speaker,
                random_choice=Mock(return_value="paper"),
            )
        )
        self.speaker.assert_called_once_with(
            "You chose paper. I chose paper. It's a tie."
        )

    def test_rock_paper_scissors_reports_loss(self):
        self.assertTrue(
            respond(
                "rock paper scissors scissors",
                speaker=self.speaker,
                random_choice=Mock(return_value="rock"),
            )
        )
        self.speaker.assert_called_once_with(
            "You chose scissors. I chose rock. I win!"
        )

    def test_rock_paper_scissors_rejects_unknown_move(self):
        random_choice = Mock()
        self.assertTrue(
            respond(
                "rock paper scissors lizard",
                speaker=self.speaker,
                random_choice=random_choice,
            )
        )
        random_choice.assert_not_called()
        self.speaker.assert_called_once_with(
            "That is not a valid move. Choose rock, paper, or scissors."
        )


if __name__ == "__main__":
    unittest.main()
