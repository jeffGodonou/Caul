import sys


def speak(text):
    """Say text through the computer's local text-to-speech voice."""
    import pyttsx3

    engine = getattr(speak, "_engine", None)
    if engine is None:
        engine = pyttsx3.init()
        speak._engine = engine
    print("Caul:", text)
    engine.say(text)
    engine.runAndWait()


def listen():
    """Listen once and return recognized words, or None if they were unclear."""
    import speech_recognition as sr

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


def respond(command, speaker=speak):
    """Handle the starter commands and return False when asked to exit."""
    command = (command or "").strip()
    normalized = command.lower()

    if normalized in {"quit", "exit", "goodbye"}:
        speaker("Goodbye!")
        return False
    if normalized in {"hello", "hi", "hey"}:
        speaker("Hello! I'm Caul. Say goodbye when you want me to stop.")
        return True
    if command:
        speaker("I heard you say: " + command)
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
