#S Caul

Caul is a small Python voice assistant for your computer. We are building it
one working step at a time so each feature is understandable and testable
before moving on.

## Step 5: weather and music

This version listens for one phrase at a time, greets you, responds to "help",
"what time is it", search commands, weather lookups, and music requests, and
allows only approved apps or sites when you say "open". It refuses
unrecognized targets, keeps the browser and app launcher injectable for tests,
and exits when you say "goodbye", "quit", or "exit". Other phrases get a
helpful unknown-command response. It is intentionally small; games and other
later features are in the [learning roadmap](ROADMAP.md).

### Set up on Windows

Install Python 3.9 or newer, connect a microphone, then open PowerShell in this
project folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe caul.py
```

Speech recognition sends audio to Google's recognition service and requires an
internet connection. Caul speaks using your computer's local text-to-speech
engine.

### Check the fifth step

Run the automated checks:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Then run `caul.py` and try:

1. Say "hello" and check that Caul answers.
2. Say "what's the weather in Paris" and check that a weather search opens.
3. Say "weather" and check that Caul asks for a location.
4. Say "play lo-fi & jazz!" and check that Spotify search opens.
5. Say "open calculator" and check that the calculator opens.
6. Say "goodbye" and check that Caul exits.
7. Try again with the microphone unplugged or internet disconnected and note
   the error before changing anything.

If a check fails, first compare what you heard with the expected behavior,
then change one thing and rerun the same check. See the roadmap for the next
milestones.
