import speech_recognition as sr

recognizer = sr.Recognizer()

with sr.Microphone() as source:
    print("Cursix is listening...")
    recognizer.adjust_for_ambient_noise(source, duration=1)
    print("Speak now!")

    try:
        audio = recognizer.listen(source, timeout=10, phrase_time_limit=8)
    except sr.WaitTimeoutError:
        print("I didn't hear anything.")
        exit()

print("I heard you. Processing...")

try:
    text = recognizer.recognize_google(audio)
    print("You said:", text)

except sr.UnknownValueError:
    print("I heard you, but I couldn't understand the words.")

except sr.RequestError as e:
    print("Google speech recognition error:", e)