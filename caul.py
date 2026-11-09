import ast
import logging
import math
import operator
import os
import random
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from urllib.parse import quote, urlencode
import webbrowser


logger = logging.getLogger("caul")

MODEL_FOLDER_NAME = "vosk-model-small-en-us-0.15"


def _default_model_path():
    """Locate the Vosk model: beside this file when running from source,
    otherwise in the per-user data folder used by an installed copy."""
    beside_module = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "models", MODEL_FOLDER_NAME
    )
    if os.path.isdir(beside_module):
        return beside_module
    data_root = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(data_root, "Caul", "models", MODEL_FOLDER_NAME)


DEFAULT_VOSK_MODEL = _default_model_path()


class MicrophoneError(OSError):
    """A microphone device could not be opened or read."""


@dataclass(frozen=True)
class Settings:
    microphone_device: Optional[int] = None
    listen_timeout: float = 5
    phrase_time_limit: float = 8
    sample_rate: int = 16000
    log_level: int = logging.WARNING
    vosk_model: str = DEFAULT_VOSK_MODEL


def load_settings(environ=None):
    """Read and validate optional Caul settings from environment variables."""
    environ = os.environ if environ is None else environ

    def positive_number(name, default, convert):
        value = environ.get(name)
        if value is None:
            return default
        try:
            parsed = convert(value)
        except ValueError as error:
            raise ValueError(name + " must be a positive number.") from error
        if parsed <= 0 or not math.isfinite(parsed):
            raise ValueError(name + " must be a positive finite number.")
        return parsed

    device_value = environ.get("CAUL_MICROPHONE_DEVICE", "").strip()
    try:
        microphone_device = int(device_value) if device_value else None
    except ValueError as error:
        raise ValueError("CAUL_MICROPHONE_DEVICE must be a device number.") from error
    if microphone_device is not None and microphone_device < 0:
        raise ValueError("CAUL_MICROPHONE_DEVICE must not be negative.")

    level_name = environ.get("CAUL_LOG_LEVEL", "WARNING").upper()
    log_level = logging.getLevelName(level_name)
    if not isinstance(log_level, int):
        raise ValueError("CAUL_LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR, or CRITICAL.")

    return Settings(
        microphone_device=microphone_device,
        listen_timeout=positive_number("CAUL_LISTEN_TIMEOUT", 5, float),
        phrase_time_limit=positive_number("CAUL_PHRASE_TIME_LIMIT", 8, float),
        sample_rate=positive_number("CAUL_SAMPLE_RATE", 16000, int),
        log_level=log_level,
        vosk_model=environ.get("CAUL_VOSK_MODEL", DEFAULT_VOSK_MODEL),
    )


def calculate(expression):
    """Evaluate a basic arithmetic expression without executing arbitrary code."""
    expression = expression.lower().replace("divided by", "/")
    expression = expression.replace("multiplied by", "*")
    expression = expression.replace("times", "*")
    expression = expression.replace("plus", "+")
    expression = expression.replace("minus", "-")
    tree = ast.parse(expression, mode="eval")
    operations = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
    }

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = evaluate(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and type(node.op) in operations:
            left = evaluate(node.left)
            right = evaluate(node.right)
            return operations[type(node.op)](left, right)
        raise ValueError("Only basic arithmetic is supported.")

    result = evaluate(tree)
    if not isinstance(result, (int, float)) or not math.isfinite(result):
        raise ValueError("The result is not a finite number.")
    return result


def _format_number(value):
    return str(int(value)) if value == int(value) else str(value)


def speak(text):
    """Say text through the computer's local text-to-speech voice."""
    try:
        import pyttsx3  # pyright: ignore[reportMissingImports]
    except ImportError as exc:
        raise RuntimeError("The 'pyttsx3' package is required for speech output.") from exc

    engine = getattr(speak, "_engine", None)
    if engine is None:
        engine = pyttsx3.init()
        speak._engine = engine
    print("Caul:", text)
    engine.say(text)
    engine.runAndWait()


def _record(settings=None):
    """Record one phrase as 16-bit PCM bytes; None if no speech was heard."""
    import time

    import numpy as np
    import sounddevice as sd

    settings = settings or load_settings()
    timeout = settings.listen_timeout
    phrase_time_limit = settings.phrase_time_limit
    rate = settings.sample_rate
    block = int(rate * 0.1)
    chunks = []
    print("Listening...")
    try:
        with sd.InputStream(
            samplerate=rate,
            channels=1,
            dtype="int16",
            blocksize=block,
            device=settings.microphone_device,
        ) as stream:
            noise = np.sqrt(np.mean(stream.read(block * 5)[0].astype(np.float64) ** 2))
            threshold = max(noise * 3, 40)
            started = time.monotonic()
            speech_start = None
            quiet = 0
            while True:
                data = stream.read(block)[0]
                loud = np.sqrt(np.mean(data.astype(np.float64) ** 2)) > threshold
                now = time.monotonic()
                if speech_start is None:
                    if loud:
                        speech_start = now
                        chunks.append(data.copy())
                    elif now - started > timeout:
                        return None
                    continue
                chunks.append(data.copy())
                quiet = 0 if loud else quiet + 1
                if quiet >= 8 or now - speech_start > phrase_time_limit:
                    break
    except (OSError, sd.PortAudioError) as error:
        raise MicrophoneError("Could not access the microphone: " + str(error)) from error
    audio = np.concatenate(chunks).astype(np.float64)
    peak = np.abs(audio).max()
    if peak > 0:
        audio *= min(20000 / peak, 100)
    return audio.astype(np.int16).tobytes()


def _recognize(pcm, settings):
    """Recognize PCM audio locally with Vosk; audio never leaves the machine."""
    import json

    import vosk

    vosk.SetLogLevel(-1)
    if getattr(_recognize, "_model_path", None) != settings.vosk_model:
        if not os.path.isdir(settings.vosk_model):
            raise RuntimeError(
                "Vosk model not found at " + settings.vosk_model + ". "
                "See README.md for download instructions."
            )
        _recognize._model = vosk.Model(settings.vosk_model)
        _recognize._model_path = settings.vosk_model
    recognizer = vosk.KaldiRecognizer(_recognize._model, settings.sample_rate)
    recognizer.AcceptWaveform(pcm)
    return json.loads(recognizer.Result()).get("text", "").strip()


def listen(settings=None):
    """Listen once and return recognized words, or None if they were unclear."""
    settings = settings or load_settings()
    pcm = _record(settings)
    if pcm is None:
        return None

    text = _recognize(pcm, settings)
    if not text:
        speak("I didn't catch that. Please try again.")
        return None
    return text


def respond(
    command,
    speaker=speak,
    clock=None,
    browser=None,
    app_launcher=None,
    random_choice=random.choice,
):
    """Handle supported commands and return False when asked to exit."""
    command = (command or "").strip()
    normalized = command.lower()

    if normalized in {"quit", "exit", "goodbye"}:
        speaker("Goodbye!")
        return False
    if normalized in {"hello", "hi", "hey"}:
        speaker("Hello! I'm Caul. Say goodbye when you want me to stop.")
        return True
    if normalized in {"help", "what can you do"}:
        speaker("I can greet you, tell you the time, calculate basic arithmetic, play rock-paper-scissors, search Google or YouTube, check the weather, play music, open Calculator, Notepad, Google, or YouTube, or stop when you say goodbye.")
        return True
    if normalized in {"time", "what time is it"}:
        current_time = (clock or datetime.now)().strftime("%I:%M %p").lstrip("0")
        speaker("The current time is " + current_time + ".")
        return True
    if normalized in {"weather", "what's the weather", "what is the weather"}:
        speaker("Tell me which location you want the weather for.")
        return True
    if normalized in {
        "search for",
        "google search for",
        "search youtube for",
        "youtube search for",
    }:
        speaker("Tell me what you'd like me to search for.")
        return True

    calculation = command
    for prefix in ("calculate ", "what is ", "what's "):
        if normalized.startswith(prefix):
            calculation = command[len(prefix):].strip()
            break
    is_weather_request = normalized.startswith(
        ("what's the weather", "what is the weather")
    )
    if not is_weather_request and (
        calculation != command or normalized.startswith(("calculate", "what is", "what's"))
    ):
        if not calculation:
            speaker("Tell me what you'd like me to calculate.")
            return True
        try:
            result = calculate(calculation)
        except (SyntaxError, ValueError, TypeError, ZeroDivisionError):
            speaker("I can only calculate basic arithmetic, such as 2 plus 2.")
            return True
        speaker("The answer is " + _format_number(result) + ".")
        return True

    if normalized.startswith("rock paper scissors"):
        move = normalized[len("rock paper scissors"):].strip()
        if not move:
            speaker("Choose rock, paper, or scissors.")
            return True
        if move not in {"rock", "paper", "scissors"}:
            speaker("That is not a valid move. Choose rock, paper, or scissors.")
            return True
        computer_move = random_choice(["rock", "paper", "scissors"])
        if move == computer_move:
            outcome = "It's a tie."
        elif (move, computer_move) in {
            ("rock", "scissors"),
            ("paper", "rock"),
            ("scissors", "paper"),
        }:
            outcome = "You win!"
        else:
            outcome = "I win!"
        speaker("You chose " + move + ". I chose " + computer_move + ". " + outcome)
        return True
    search_prefixes = (
        ("search youtube for ", "youtube"),
        ("youtube search for ", "youtube"),
        ("google search for ", "google"),
        ("search for ", "google"),
    )
    for prefix, service in search_prefixes:
        if normalized.startswith(prefix):
            query = command[len(prefix):].strip()
            if not query:
                speaker("Tell me what you'd like me to search for.")
                return True
            if service == "youtube":
                url = "https://www.youtube.com/results?" + urlencode({"search_query": query})
            else:
                url = "https://www.google.com/search?" + urlencode({"q": query})
            open_url = browser if browser is not None else webbrowser.open
            open_url(url)
            service_name = "YouTube" if service == "youtube" else "Google"
            speaker("Searching " + service_name + " for " + query + ".")
            return True

    weather_prefixes = (
        "weather in ",
        "what's the weather in ",
        "what is the weather in ",
    )
    for prefix in weather_prefixes:
        if normalized.startswith(prefix):
            location = command[len(prefix):].strip()
            if not location:
                speaker("Tell me which location you want the weather for.")
                return True
            open_url = browser if browser is not None else webbrowser.open
            open_url("https://www.google.com/search?" + urlencode({"q": "weather " + location}))
            speaker("Checking the weather in " + location + ".")
            return True

    if normalized.startswith("play "):
        song = command[len("play "):].strip()
        if not song:
            speaker("What song would you like me to play?")
            return True
        open_url = browser if browser is not None else webbrowser.open
        open_url("https://open.spotify.com/search/" + quote(song, safe=""))
        speaker("Playing " + song + " on Spotify.")
        return True

    if normalized.startswith("open "):
        target = normalized[len("open "):].strip()
        apps = {
            "calculator": ["calc.exe"],
            "notepad": ["notepad.exe"],
        }
        websites = {
            "google": "https://www.google.com/",
            "youtube": "https://www.youtube.com/",
        }
        labels = {
            "calculator": "Calculator",
            "notepad": "Notepad",
            "google": "Google",
            "youtube": "YouTube",
        }
        if target in apps:
            launch = app_launcher if app_launcher is not None else subprocess.Popen
            launch(apps[target])
            speaker("Opening " + labels[target] + ".")
            return True
        if target in websites:
            open_url = browser if browser is not None else webbrowser.open
            open_url(websites[target])
            speaker("Opening " + labels[target] + ".")
            return True
        speaker("I can only open Calculator, Notepad, Google, or YouTube.")
        return True
    if command:
        speaker("I don't know that command. Say help to hear what I can do.")
    return True


def main(settings=None):
    try:
        settings = settings or load_settings()
        logging.basicConfig(
            level=settings.log_level,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
        speak("Caul is ready. Say hello, or say goodbye to stop.")
        while True:
            command = listen(settings)
            if command is not None and not respond(command):
                break
    except KeyboardInterrupt:
        speak("Goodbye!")
    except (OSError, ImportError, RuntimeError, ValueError) as error:
        logger.exception("Caul could not start or access its audio devices.")
        print("Caul audio/setup error:", error, file=sys.stderr)
        print(
            "Check the setup and microphone troubleshooting steps in README.md.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
