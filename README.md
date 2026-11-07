#S Caul

Caul is a small Python voice assistant for your computer. We are building it
one working step at a time so each feature is understandable and testable
before moving on.

## Milestone 7: dependable startup and recovery

Caul listens for one phrase at a time, greets you, responds to "help", tells
the time, calculates basic arithmetic, plays rock-paper-scissors, searches
Google or YouTube, checks the weather, searches Spotify, and opens only
approved apps or sites. Say "goodbye", "quit", or "exit" to stop. See the
[learning roadmap](ROADMAP.md) for how the project was built.

### Set up on Windows

Install Python 3.9 or newer, connect a microphone, then open PowerShell in the
project folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe caul.py
```

Speech recognition runs locally with [Vosk](https://alphacephei.com/vosk/) —
your audio never leaves the computer, and no internet connection is needed to
understand you. Caul speaks using your computer's local text-to-speech engine.
An internet connection is only needed when a command opens a web page.

The first time you set up the project, download the small English model
(about 40 MB) into the `models` folder:

```powershell
curl.exe -L -o "$env:TEMP\vosk-model.zip" "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
Expand-Archive "$env:TEMP\vosk-model.zip" models
Remove-Item "$env:TEMP\vosk-model.zip"
```

### Settings and troubleshooting

Defaults work with the Windows default microphone. To choose a different
microphone, first list available device names and numbers:

```powershell
.\.venv\Scripts\python.exe -c "import sounddevice as sd; print(sd.query_devices())"
$env:CAUL_MICROPHONE_DEVICE = "2"
.\.venv\Scripts\python.exe caul.py
```

Replace `2` with the input device number from the list. These optional
environment settings can be set in PowerShell before starting Caul:

| Setting | Default | Purpose |
| --- | --- | --- |
| `CAUL_MICROPHONE_DEVICE` | system default | Input device number |
| `CAUL_LISTEN_TIMEOUT` | `5` | Seconds to wait for speech to begin |
| `CAUL_PHRASE_TIME_LIMIT` | `8` | Maximum seconds recorded per phrase |
| `CAUL_SAMPLE_RATE` | `16000` | Microphone sample rate in Hz |
| `CAUL_LOG_LEVEL` | `WARNING` | Optional diagnostics: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` |
| `CAUL_VOSK_MODEL` | `models/vosk-model-small-en-us-0.15` | Path to the Vosk speech model |

If Windows reports that no input device is available, connect or enable a
microphone in Windows Sound settings, select its device number as shown above,
and restart Caul. If Caul reports that the Vosk model is missing, run the
download commands above or point `CAUL_VOSK_MODEL` at an unpacked model from
the [Vosk model list](https://alphacephei.com/vosk/models). Use
`CAUL_LOG_LEVEL=INFO` to see diagnostic messages. Caul does not log spoken
phrases.

### Check milestone 7

Run the automated checks from the project folder:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Then start Caul and try:

1. Say "hello" and check that Caul answers.
2. Say "what's the weather in Paris" and check that a weather search opens.
3. Say "weather" and check that Caul asks for a location.
4. Say "play lo-fi & jazz!" and check that Spotify search opens.
5. Say "open calculator" and check that the calculator opens.
6. Say "calculate 12 divided by 3" and check that Caul says 4.
7. Say "rock paper scissors rock" and check that Caul reports the outcome.
8. Say "goodbye" and check that Caul exits.
9. Disconnect from the internet and say "hello" — recognition is offline, so
   Caul should still answer. Web commands will open pages that cannot load
   until you reconnect.
10. If practical, select an unavailable microphone device and confirm Caul
    reports the setup problem and exits cleanly. Restore the working device
    setting before starting Caul again.
11. Set `$env:CAUL_LOG_LEVEL = "INFO"` and confirm diagnostic logs appear;
    clear it with `Remove-Item Env:CAUL_LOG_LEVEL` afterward.

If a check fails, first compare what you heard with the expected behavior,
then change one thing and rerun the same check. Full build notes are in the
[roadmap](ROADMAP.md).
