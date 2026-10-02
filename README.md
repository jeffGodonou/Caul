#S Caul

Caul is a small Python voice assistant for your computer. We are building it
one working step at a time so each feature is understandable and testable
before moving on.

## Step 2: recognize commands

This version listens for one phrase at a time, greets you, responds to "help"
and "what time is it", and exits when you say "goodbye", "quit", or "exit".
Other phrases get a helpful unknown-command response. It is intentionally
small; web search, weather, music, and games are later steps in the
[learning roadmap](ROADMAP.md).

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

### Check the first step

Run the automated checks:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Then run `caul.py` and try:

1. Say "hello" and check that Caul answers.
2. Say "help" and check that Caul lists its supported actions.
3. Say "what time is it" and check that Caul reports the time.
4. Say an unrelated phrase and check that Caul suggests "help".
5. Say "goodbye" and check that Caul exits.
6. Try again with the microphone unplugged or internet disconnected and note
   the error before changing anything.

If a check fails, first compare what you heard with the expected behavior,
then change one thing and rerun the same check. See the roadmap for the next
milestones.
