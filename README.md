#S Caul

Caul is a small Python voice assistant for your computer. We are building it
one working step at a time so each feature is understandable and testable
before moving on.

## Step 1: run the voice loop

This first version listens for one phrase at a time, greets you, repeats other
phrases, and exits when you say "goodbye", "quit", or "exit". It is intentionally
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
2. Say a short sentence and check that Caul repeats it.
3. Say "goodbye" and check that Caul exits.
4. Try again with the microphone unplugged or internet disconnected and note
   the error before changing anything.

If a check fails, first compare what you heard with the expected behavior,
then change one thing and rerun the same check. See the roadmap for the next
milestones.
