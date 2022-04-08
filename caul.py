# import required modules

import speech_recognition as sr
import playsound #play an audio
import random
from gtts import gTTS # google text to speech
import webbrowser
import ssl
import certifi
import time
import os #remove the audio files
from PIL import Image
import pyautogui
import pyttsx3
import bs4 as bs
import urllib.request 
  
class person:
    name=''
    def setName(self,name):
        self.name=name

class asis:
    name=''
    def setName(self,name):
        self.name=name

def there_exists(terms):
    for term in terms:
        if term in voice_data:
            return True
 
def engine_speak(text):
    text= str(text)
    engine.say(text)
    engine.runAndWait()

r=sr.Recognizer()

def record_audio(ask=""):
    with sr.Microphone() as source:
        if ask:
            engine_speak(ask)
        audio= r.listen(source)
        print("Done Listening")
        voice_data=""
        try:
            voice_data= r.recognize_google(audio)
        except sr.UnknownValueError:
            engine_speak("Sorry sir, I don't understand that, can you retry")
        except sr.RequestError:
            engine_speak("Sorry, the server can't reached out")
            print(">>", voice_data.lower())
            return voice_data.lower()

def engine_speak(audio_string):
    audio_string = str(audio_string)
    tts = gTTS( text = audio_string, lang ='en')
    r = random.randint(1,20000000)
    audio_file = 'audio' + str(r) + '.mp3'
    tts.save(audio_file)

    playsound.playsound(audio_file)
    print(asis_obj.name + ":", audio_string)
    os.remove(audio_file)

def respond(voice_data):
    # greetings
    if there_exists(['hello','hi','allo','hey','hola','bonjour','bonsoir']):
        greetings=['hey, I hope you are ok, how can I help you' + person_obj.name, 'how can I help you' + person_obj.name, 'hello' + person_obj.name, 'hello, hope you had a great day' + person_obj.name]
        greet  = greetings[random.randint(0,len(greetings)-1)]
        engine_speak(greet)
    
    # name
    if there_exists(['what is your name', 'tell me your name', 'who are you?']):
        if person_obj.name:
            engine_speak('I am Caul, at your service')
        else:
            engine_speak('What is your name')
    
    if there_exists(["I am"]):
        person_name=voice_data.split("am")[-1].strip()
        engine_speak("ok, I'll remember that your name is " + person_name())
        person_obj.setName(person_name)
    
    if there_exists(["my name is"]):
        person_name=voice_data.split("is")[-1].strip()
        engine_speak("ok, I'll remember that your name is " + person_name())
        person_obj.setName(person_name)
    
    #greetings
    if there_exists(["how are you", "how are you doing"]):
        answers=(["I am very well thanks", "I am doing just fine", "I am having a moment", "I am sensing my cpu is having a blast"])
        greet  = answers[random.randint(0,len(answers)-1)]
        engine_speak(greet)
    
    #time
    if there_exists(["what time is it", "what the time", "can you tell me time"]):
        time=time.ctime().split(" ")[3].split(":")[0:2]
        if time[0]=="00":
            hours='12'
        else:
            hours=time[0]
            minutes=time[1]
            time=hours+"hour and" + minutes + "minutes"
            engine_speak(time)
    
    #google search
    if there_exists(["search for"]) and 'youtube' not in voice_data:
        search_term= voice_data.split("for")[-1]
        url="https://google.com/search?q"+search_term
        webbrowser.get().open(url)
        engine_speak("Here is what I found for" + search_term + "on google" )
    
    #youtube search
    if there_exists(["youtube"]):
        search_term = voice_data.split("for")[-1]
        url="https://www.youtube.com/results?search_query="+search_term
        webbrowser.get().open(url)
        engine_speak("Here is what I found for" + search_term + "on youtube" )
    
    # stock market price
    if there_exists(["price of"]):
        search_term = voice_data.split("for")[-1]
        url="https://google.com/search?q"+search_term
        webbrowser.get().open(url)
        engine_speak("Here is what I found for" + search_term + "on google" )

    # search for music
    if there_exists(["play music"]):
        search_term = voice_data.split("for")[-1]
        url="thhps://open.spotify.com/search/"+search_term
        webbrowser.get().open(url)
        engine_speak("You are listening to" + search_term + "enjoy")
        
    # search for amazon.com
    if there_exists(["amazon.com"]):
        search_term = voice_data.split("for")[-1]
        url = "https://www.amazon.in" + search_term
        webbrowser.get().open(url)
        engine_speak("Here is what I found for" + search_term + "on amazon.com")

    # make a note 
    if there_exists(["make a note"]):
        search_term = voice_data.split("for")[-1]
        url = "https://keep.google.com/#home"
        webbrowser.get().open(url)
        engine_speak("What do you want me to take in note")
    
    # open instagram
    if there_exists(["open Instagram", "navigate throught my Instagram feed"]):
        search_term = voice_data.split("for")[-1]   
        url = "https://www.instagram.com"
        webbrowser.get().open(url)
        engine_speak("opening Instagram")

    # open twitter
    if there_exists(["open twitter", "twitt"]):
        search_term = voice_data.split("for")[-1]
        url = "https://twitter.com/"
        webbrowser.get().open(url)
        engine_speak("opening twitter")
    
    # weather
    if there_exists(["weather", "tell me the weather report", "what's the condition outside", "what's the weather today"]):
        search_term = voice_data.split("for")[-1]
        url = "https://www.google.com/search?sxsrf=ACYBGNSQwMLDByBwdVFIUCbQqya-ET7AAA%3A1578847393212&ei=oUwbXtbXDN-C4-EP-5u82AE&q=weather&oq=weather&gs_l=psy-ab.3..35i39i285i70i256j0i67l4j0i131i67j0i131j0i67l2j0.1630.4591..5475...1.2..2.322.1659.9j5j0j1......0....1..gws-wiz.....10..0i71j35i39j35i362i39._5eSPD47bv8&ved=0ahUKEwiWrJvwwP7mAhVfwTgGHfsNDxsQ4dUDCAs&uact=5"
        webbrowser.get().open(url)
        engine_speak("it is")

    # open gmail
    if there_exists(["open my mail", "gmail", "check my mail"]):
        search_term = voice_data.split("for")[-1]
        url = "https://mail.google.com/mail/u/0/#inbox"
        webbrowser.get().open(url)
        engine_speak("here is your last mails")

    # game 

    # rock, paper, scissors
    if there_exists(["game"]):
        voice_data = record_audio("choose among rock, paper or scissor")
        moves = ["rock", "paper", "scissor"]
        cmove = random.choice(moves)
        pmove = voice_data
        engine_speak("I chose" + cmove)

        if pmove == cmove:
            engine_speak("The match draw")
        elif pmove == "rock" and cmove == "paper":
            engine_speak("I win, yeah")
        elif pmove == "paper" and cmove == "scissor":
            engine_speak("I win")
        elif pmove == "scissor" and cmove == "paper":
            engine_speak("You win, good choice")
        elif pmove == "paper" and cmove == "rock":
            engine_speak("You win, well read")
        elif pmove == "rock" and cmove == "scissor":
            engine_speak("You win, awesomwe")
        elif pmove == "scissor" and cmove == "rock":
            engine_speak("I win, cool")

    # calculator
    if there_exists(["plus", "minus", "multiply", "divide", "power", "square", "+", "-", "*", "/"]):
        opr = voice_data.split()[1]

        if opr == '+':
            engine_speak(int(voice_data.split()[0] + int(voice_data.split()[2])))
 
        
        elif opr == '-':
            engine_speak(int(voice_data.split()[0] - int(voice_data.split()[2])))
        elif opr == '*':
            engine_speak(int(voice_data.split()[0] * int(voice_data.split()[2])))
        elif opr == '/':
            engine_speak(int(voice_data.split()[0] / int(voice_data.split()[2])))
        elif opr == 'power':
            engine_speak(int(voice_data.split()[0] ** int(voice_data.split()[2])))
        elif opr == 'square':
            engine_speak(int(voice_data.split()[0] ** (0.5)))
        else:
            engine_speak("This operation is not valid")
        
    # Quit
    if there_exists(["exit", "quit", "goodbye"]):
        engine_speak("we could continue more sir, but.,,...,,,,,..,,,,, byee")
        exit()

time.sleep(1)

person_obj = person()
asis_obj = asis()
asis_obj.name = 'Caul'
engine = pyttsx3.init()


while(1):
    voice_data = record_audio("Recording") # get the voice input
    print("Done")
    print("Q:", voice_data)
    respond(voice_data) # respond

     
    