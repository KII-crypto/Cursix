import pyttsx3

engine = pyttsx3.init()

engine.setProperty("rate", 170)
engine.setProperty("volume", 1.0)

voices = engine.getProperty("voices")

for voice in voices:
    print(voice.id)

engine.say("Good evening, Brilliant. I am Cursix.")
engine.runAndWait()