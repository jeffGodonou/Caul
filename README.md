# Caul — Voice Assistant

A Python-based voice assistant that listens to spoken commands and responds using text-to-speech. Caul can answer questions, search the web, play music, check the weather, open apps, and even play games — all hands-free.

---

## Features

- **Speech recognition** — listens to your voice using your microphone
- **Text-to-speech responses** — replies out loud using Google TTS
- **Web search** — searches Google or YouTube on command
- **App shortcuts** — opens Gmail, Instagram, Twitter, Amazon, Google Keep
- **Weather** — pulls up current weather information
- **Music** — searches and opens Spotify
- **Calculator** — handles basic arithmetic operations by voice
- **Rock, Paper, Scissors** — voice-controlled game against the assistant
- **Personalization** — remembers your name during the session

---

## Tech Stack

- **Language:** Python 3
- **Speech recognition:** `SpeechRecognition`
- **Text-to-speech:** `gTTS` (Google Text-to-Speech), `pyttsx3`
- **Audio playback:** `playsound`
- **Browser control:** `webbrowser`
- **Other:** `pyautogui`, `Pillow`, `BeautifulSoup4`, `ssl`, `certifi`

---

## Getting Started

### Prerequisites

- Python 3.7+
- A working microphone
- pip

### Install dependencies

```bash
pip install speechrecognition gtts pyttsx3 playsound pyautogui Pillow beautifulsoup4 urllib3 certifi
```

### Run the assistant

```bash
python caul.py
```

Caul will start listening immediately. Speak a command and it will respond.

---

## Example Commands

| What you say | What Caul does |
|---|---|
| `"Hello"` / `"Hey"` | Greets you by name |
| `"What is your name?"` | Introduces itself |
| `"Search for Python tutorials"` | Opens Google search |
| `"YouTube for lofi music"` | Opens YouTube search |
| `"Play music for jazz"` | Opens Spotify search |
| `"What time is it?"` | Tells you the current time |
| `"What's the weather today?"` | Opens weather results |
| `"Open Gmail"` | Opens your Gmail inbox |
| `"Let's play a game"` | Starts Rock, Paper, Scissors |
| `"5 plus 3"` | Returns the result out loud |
| `"Exit"` / `"Goodbye"` | Shuts down the assistant |

---

## Known Limitations

- Requires an active internet connection for Google TTS and web searches
- Speech recognition accuracy depends on microphone quality and background noise
- The MP3 audio files generated during TTS are created and deleted automatically in the working directory

---

## Author

**Jeff Godonou** — [github.com/jeffGodonou](https://github.com/jeffGodonou)
