import sys
from datetime import datetime
from urllib.parse import urlencode
import webbrowser

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


def listen():
    """Listen once and return recognized words, or None if they were unclear."""
    from importlib import import_module

    sr = import_module("speech_recognition")

    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as microphone:
            recognizer.adjust_for_ambient_noise(microphone, duration=0.5)
            print("Listening...")
            audio = recognizer.listen(microphone, timeout=5, phrase_time_limit=8)
    except sr.WaitTimeoutError:
        return None

    try:
        return recognizer.recognize_google(audio).strip()
    except sr.UnknownValueError:
        speak("I didn't catch that. Please try again.")
        return None
    except sr.RequestError as error:
        print("Speech recognition service error:", error, file=sys.stderr)
        speak("I can't reach the speech recognition service right now.")
        return None


def respond(command, speaker=speak, clock=None, browser=None):
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
        speaker("I can greet you, tell you the time, search Google or YouTube, or stop when you say goodbye.")
        return True
    if normalized in {"time", "what time is it"}:
        current_time = (clock or datetime.now)().strftime("%I:%M %p").lstrip("0")
        speaker("The current time is " + current_time + ".")
        return True
    if normalized in {
        "search for",
        "google search for",
        "search youtube for",
        "youtube search for",
    }:
        speaker("Tell me what you'd like me to search for.")
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
    if command:
        speaker("I don't know that command. Say help to hear what I can do.")
    return True


def main():
    speak("Caul is ready. Say hello, or say goodbye to stop.")
    try:
        while True:
            command = listen()
            if command is not None and not respond(command):
                break
    except KeyboardInterrupt:
        speak("Goodbye!")
    except (OSError, ImportError) as error:
        print("Microphone or audio setup error:", error, file=sys.stderr)
        print("Check the setup steps in README.md.", file=sys.stderr)


if __name__ == "__main__":
    main()
