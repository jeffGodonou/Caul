import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from caul import Settings, main, respond


class NoteCommandTests(unittest.TestCase):
    def test_dictated_note_is_written_as_utf8_and_opened(self):
        speaker = Mock()
        launcher = Mock()
        listener = Mock(return_value="  Buy tea & café supplies  ")
        with tempfile.TemporaryDirectory() as directory:
            with patch("caul_commands.tempfile.tempdir", directory):
                self.assertTrue(respond(
                    "create a note", speaker=speaker, listener=listener,
                    app_launcher=launcher,
                ))
            listener.assert_called_once_with()
            executable, path = launcher.call_args.args[0]
            self.assertEqual(executable, "notepad.exe")
            self.assertEqual(os.path.dirname(path), directory)
            self.assertTrue(path.endswith(".txt"))
            with open(path, encoding="utf-8") as note_file:
                self.assertEqual(note_file.read(), "Buy tea & café supplies")
        self.assertIn("Save As", speaker.call_args.args[0])

    def test_cancel_empty_and_exit_do_not_create_note(self):
        for answer, expected in ((None, True), ("  ", True), ("cancel", True), ("goodbye", False)):
            with self.subTest(answer=answer), tempfile.TemporaryDirectory() as directory:
                with patch("caul_commands.tempfile.tempdir", directory):
                    launcher = Mock()
                    self.assertEqual(respond(
                        "take a note", speaker=Mock(), listener=Mock(return_value=answer),
                        app_launcher=launcher,
                    ), expected)
                    launcher.assert_not_called()
                    self.assertEqual(os.listdir(directory), [])

    def test_start_document_opens_blank_notepad(self):
        launcher = Mock()
        speaker = Mock()
        self.assertTrue(respond("start a document", speaker=speaker, app_launcher=launcher))
        launcher.assert_called_once_with(["notepad.exe"])
        speaker.assert_called_once_with("Opening a blank document in Notepad.")

    def test_failed_launch_reports_location_of_note(self):
        speaker = Mock()
        with tempfile.TemporaryDirectory() as directory:
            with patch("caul_commands.tempfile.tempdir", directory):
                with self.assertLogs("caul", level="ERROR"):
                    self.assertTrue(respond(
                        "create a note", speaker=speaker, listener=Mock(return_value="My note"),
                        app_launcher=Mock(side_effect=OSError("Notepad unavailable")),
                    ))
            paths = os.listdir(directory)
            self.assertEqual(len(paths), 1)
            self.assertIn(os.path.join(directory, paths[0]), speaker.call_args.args[0])
            with open(os.path.join(directory, paths[0]), encoding="utf-8") as note_file:
                self.assertEqual(note_file.read(), "My note")

    def test_failed_note_creation_is_reported_without_launch(self):
        speaker = Mock()
        launcher = Mock()
        with patch("caul_commands.tempfile.NamedTemporaryFile", side_effect=OSError("disk full")):
            with self.assertLogs("caul", level="ERROR"):
                self.assertTrue(respond(
                    "create a note", speaker=speaker, listener=Mock(return_value="My note"),
                    app_launcher=launcher,
                ))
        launcher.assert_not_called()
        self.assertIn("couldn't write the note", speaker.call_args.args[0])

    def test_main_uses_current_settings_for_note_dictation(self):
        settings = Settings(microphone_device=2)
        listener = Mock(side_effect=["create a note", "Meeting notes", "goodbye"])
        launcher = Mock()
        speaker = Mock()
        with tempfile.TemporaryDirectory() as directory:
            with patch("caul_commands.tempfile.tempdir", directory), patch(
                "caul.listen", listener
            ), patch("caul.speak", speaker), patch(
                "caul.respond",
                side_effect=lambda command, **kwargs: respond(
                    command, speaker=speaker, app_launcher=launcher, **kwargs
                ),
            ):
                main(settings, alert_manager=Mock())
        self.assertEqual(listener.call_args_list, [unittest.mock.call(settings)] * 3)
        launcher.assert_called_once()


if __name__ == "__main__":
    unittest.main()
