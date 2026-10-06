#S Caul

Caul is a small Python voice assistant for your computer. We are building it
one working step at a time so each feature is understandable and testable
before moving on.

## Step 4: open approved apps and websites

This version listens for one phrase at a time, greets you, responds to "help"
and "what time is it", searches Google when you say "search for" and YouTube
when you say "search YouTube for", and opens Calculator, Notepad, Google, or
YouTube when you say "open" followed by an approved target. Other open requests
are refused. Caul exits when you say "goodbye", "quit", or "exit". It is
intentionally small; weather, music, and games are later steps in the
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

### Check the fourth step

Run the automated checks:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Then run `caul.py` and try:

1. Say "hello" and check that Caul answers.
2. Say "open Calculator" and "open Notepad" and check that each app opens.
3. Say "open Google" and "open YouTube" and check that each website opens.
4. Say "open Paint" and check that Caul refuses the unapproved app.
5. Say "search for cats and dogs" and check that Google opens.
6. Say "search YouTube for lo-fi music" and check that YouTube opens.
7. Say "what time is it" and check that Caul reports the time.
8. Say an unrelated phrase and check that Caul suggests "help".
9. Say "goodbye" and check that Caul exits.
10. Try again with the microphone unplugged or internet disconnected and note
   the error before changing anything.

If a check fails, first compare what you heard with the expected behavior,
then change one thing and rerun the same check. See the roadmap for the next
milestones.
