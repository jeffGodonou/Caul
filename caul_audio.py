"""Microphone capture, local speech recognition, and speech output."""

import logging
import os

from caul_settings import Settings, load_settings


logger = logging.getLogger("caul")


class MicrophoneError(OSError):
    """A microphone device could not be opened or read."""


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
            # Scale the speech threshold to ambient noise, with a quiet-room floor.
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
        # Normalize quieter microphones without amplifying beyond the PCM range.
        audio *= min(20000 / peak, 100)
    return audio.astype(np.int16).tobytes()


def _recognize(pcm, settings):
    """Recognize PCM audio locally with Vosk; audio never leaves the machine."""
    import json

    model_path = getattr(_recognize, "_model_path", None)
    # Check the model path before importing Vosk to give a setup error first.
    if model_path != settings.vosk_model and not os.path.isdir(settings.vosk_model):
        raise RuntimeError(
            "Vosk model not found at " + settings.vosk_model + ". "
            "See README.md for download instructions."
        )
    import vosk

    vosk.SetLogLevel(-1)
    if model_path != settings.vosk_model:
        # Reuse the loaded model while the configured path remains unchanged.
        _recognize._model = vosk.Model(settings.vosk_model)
        _recognize._model_path = settings.vosk_model
    recognizer = vosk.KaldiRecognizer(_recognize._model, settings.sample_rate)
    recognizer.AcceptWaveform(pcm)
    return json.loads(recognizer.Result()).get("text", "").strip()


def listen(settings=None, recorder=None, recognizer=None, speaker=None):
    """Listen once and return recognized words, or None if they were unclear."""
    settings = settings or load_settings()
    pcm = (recorder or _record)(settings)
    if pcm is None:
        return None

    text = (recognizer or _recognize)(pcm, settings)
    if not text:
        (speaker or speak)("I didn't catch that. Please try again.")
        return None
    return text
