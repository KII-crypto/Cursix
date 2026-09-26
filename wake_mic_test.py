import openwakeword
from openwakeword.model import Model
import pyaudio
import numpy as np

print("Loading Cursix wake-word system...")

openwakeword.utils.download_models()

model = Model(
    wakeword_models=["hey_jarvis"]
)

audio = pyaudio.PyAudio()

stream = audio.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    input=True,
    frames_per_buffer=1280
)

print("Cursix is listening for the test wake word.")
print("Say: Hey Jarvis")
print("Press Ctrl+C to stop.")

try:
    while True:
        data = stream.read(1280, exception_on_overflow=False)
        audio_data = np.frombuffer(data, dtype=np.int16)

        prediction = model.predict(audio_data)

        score = prediction.get("hey_jarvis", 0)

        if score > 0.5:
            print("Wake word detected! Score:", score)

except KeyboardInterrupt:
    print("\nTest stopped.")

finally:
    stream.stop_stream()
    stream.close()
    audio.terminate()