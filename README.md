# Caul

**A private, offline voice assistant for Windows.**

Caul listens for a spoken command, understands it entirely on your machine,
and answers with your computer's own voice. No audio ever leaves your device —
speech recognition runs locally with [Vosk](https://alphacephei.com/vosk/),
and text-to-speech uses the Windows voice engine. An internet connection is
only used when a command opens a web page.

## Features

- **Offline speech recognition** — your voice is never sent to a cloud service
- **Local text-to-speech** — answers through the built-in Windows voice
- **Voice commands** — time, arithmetic, rock-paper-scissors, Google/YouTube
  search, weather lookup, Spotify search, and opening approved apps
- **Safe by default** — only allowlisted apps and sites can be opened; spoken
  input is never executed as a shell command
- **Configurable** — microphone, timing, and logging via environment variables
- **Dependable** — clear recovery from microphone and setup problems

## Install

### Download (no Python required)

1. Download `caul-0.7.0-windows-x64.zip` from
   [Releases](https://github.com/jeffGodonou/Caul/releases).
2. Unzip it and run `caul.exe`.

The speech model is bundled, so it works offline on first run. The executable
is unsigned, so Windows SmartScreen may ask you to confirm.

### From source

Requires Python 3.13 or newer and a microphone.

```powershell
git clone https://github.com/jeffGodonou/Caul.git
cd Caul
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Download the speech model (about 40 MB) into the `models` folder:

```powershell
curl.exe -L -o "$env:TEMP\vosk-model.zip" "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
Expand-Archive "$env:TEMP\vosk-model.zip" models
Remove-Item "$env:TEMP\vosk-model.zip"
```

Then start Caul:

```powershell
.\.venv\Scripts\caul.exe
```

## Usage

Start Caul, wait for "Caul is ready", then speak. Say **"goodbye"** (or
"quit" / "exit") to stop.

| Say | Caul does |
| --- | --- |
| "hello" | Greets you |
| "help" | Lists what it can do |
| "what time is it" | Tells the current time |
| "calculate 12 divided by 3" | Answers 4 |
| "rock paper scissors rock" | Plays a round |
| "search for …" / "search YouTube for …" | Opens a Google / YouTube search |
| "what's the weather in Paris" | Opens a weather search |
| "play lo-fi & jazz" | Opens a Spotify search |
| "open calculator" / "open notepad" / "open google" / "open youtube" | Opens the app or site |

## Configuration

Caul works out of the box with the default microphone. Optional environment
variables (set in PowerShell before starting):

| Variable | Default | Purpose |
| --- | --- | --- |
| `CAUL_MICROPHONE_DEVICE` | system default | Input device number |
| `CAUL_LISTEN_TIMEOUT` | `5` | Seconds to wait for speech to begin |
| `CAUL_PHRASE_TIME_LIMIT` | `8` | Maximum seconds recorded per phrase |
| `CAUL_SAMPLE_RATE` | `16000` | Microphone sample rate in Hz |
| `CAUL_LOG_LEVEL` | `WARNING` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` |
| `CAUL_VOSK_MODEL` | bundled / `models/…` | Path to a Vosk speech model |

To pick a specific microphone, list devices and set its number:

```powershell
.\.venv\Scripts\python.exe -c "import sounddevice as sd; print(sd.query_devices())"
$env:CAUL_MICROPHONE_DEVICE = "2"
```

## Troubleshooting

- **"No input device" / microphone errors** — connect or enable a microphone
  in Windows Sound settings, select its device number as above, and restart.
- **"Vosk model not found"** — run the model download commands above, or point
  `CAUL_VOSK_MODEL` at an unpacked model from the
  [Vosk model list](https://alphacephei.com/vosk/models).
- **Diagnostics** — set `$env:CAUL_LOG_LEVEL = "INFO"` for detailed logs.
  Caul never logs spoken phrases.

## Development

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Every push and pull request runs the test suite on GitHub Actions
(`windows-latest`, Python 3.13). Tests mock speech recognition, so CI needs
no microphone or model.

Pushing a version tag (for example `v0.8.0`) additionally builds the
standalone executable and publishes a GitHub Release with the zipped app
attached — see [.github/workflows/ci.yml](.github/workflows/ci.yml).

To build the standalone executable yourself:

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --name caul `
  --add-data "models/vosk-model-small-en-us-0.15;models/vosk-model-small-en-us-0.15" `
  --collect-all vosk --collect-all sounddevice --collect-all pyttsx3 --collect-all comtypes `
  caul.py
```

The result is `dist\caul\caul.exe`.

## Privacy

Caul records audio only while listening for a command, processes it locally,
and discards it immediately. Nothing is transmitted or stored. Web commands
open pages in your browser, which then connect to those services as usual.

## License

[MIT](LICENSE)
