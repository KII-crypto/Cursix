import speech_recognition as sr
import pyaudio
import keyboard
import tkinter as tk
import threading
import subprocess
import difflib
import requests
import psutil
import time
import os
from datetime import datetime


# ============================================================
# CURSIX STATE
# ============================================================

running = True
shutdown_requested = False
space_pressed = False

window = None
status_label = None


# ============================================================
# VOICE
# ============================================================

def speak(text):

    print("Cursix:", text)

    safe_text = str(text).replace('"', "'")

    command = (
        'Add-Type -AssemblyName System.Speech; '
        '$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
        '$speaker.Volume = 100; '
        '$speaker.Rate = 0; '
        f'$speaker.Speak("{safe_text}"); '
        '$speaker.Dispose()'
    )

    try:

        subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                command
            ],
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    except Exception as error:

        print(
            "Voice error:",
            error
        )


# ============================================================
# ASYNC VOICE
# ============================================================

def speak_async(text):

    thread = threading.Thread(
        target=speak,
        args=(text,),
        daemon=True
    )

    thread.start()


# ============================================================
# WINDOW UPDATE
# ============================================================

def update_window(text):

    global window
    global status_label

    if window is None:
        return

    try:

        window.after(
            0,
            lambda: status_label.config(
                text=text
            )
        )

    except Exception:
        pass


# ============================================================
# SHUTDOWN CURSIX
# ============================================================

def shutdown_cursix():

    global running
    global shutdown_requested

    if shutdown_requested:
        return

    shutdown_requested = True
    running = False

    print()
    print(
        "Cursix shutting down..."
    )

    update_window(
        "GOODBYE"
    )

    speak_async(
        "Goodbye."
    )

    if window is not None:

        window.after(
            1500,
            window.destroy
        )


# ============================================================
# SPACEBAR
# ============================================================

def space_down(event):

    global space_pressed

    if not space_pressed:

        space_pressed = True


def space_up(event):

    global space_pressed

    space_pressed = False


# ============================================================
# CREATE WINDOW
# ============================================================

def create_window():

    global window
    global status_label

    window = tk.Tk()

    window.title(
        "CURSIX"
    )

    window.geometry(
        "520x320"
    )

    window.resizable(
        False,
        False
    )

    window.configure(
        bg="#10141f"
    )

    window.attributes(
        "-topmost",
        True
    )


    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    title = tk.Label(
        window,
        text="CURSIX",
        font=(
            "Segoe UI",
            32,
            "bold"
        ),
        fg="#00bfff",
        bg="#10141f"
    )

    title.pack(
        pady=(35, 5)
    )


    # --------------------------------------------------------
    # SUBTITLE
    # --------------------------------------------------------

    subtitle = tk.Label(
        window,
        text="PERSONAL VOICE ASSISTANT",
        font=(
            "Segoe UI",
            9
        ),
        fg="#8793a5",
        bg="#10141f"
    )

    subtitle.pack(
        pady=(0, 25)
    )


    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    status_label = tk.Label(
        window,
        text="READY",
        font=(
            "Segoe UI",
            21,
            "bold"
        ),
        fg="#00ff88",
        bg="#10141f"
    )

    status_label.pack()


    # --------------------------------------------------------
    # INSTRUCTION
    # --------------------------------------------------------

    instruction = tk.Label(
        window,
        text="Hold SPACE to speak • Release when finished",
        font=(
            "Segoe UI",
            11
        ),
        fg="#aab4c3",
        bg="#10141f"
    )

    instruction.pack(
        pady=(25, 0)
    )


    # --------------------------------------------------------
    # X BUTTON
    # --------------------------------------------------------

    window.protocol(
        "WM_DELETE_WINDOW",
        shutdown_cursix
    )


# ============================================================
# APPLICATION DISCOVERY
# ============================================================

def get_installed_apps():

    apps = {}

    try:

        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                "Get-StartApps | "
                "ForEach-Object { "
                "$_.Name + '|' + $_.AppID "
                "}"
            ],
            capture_output=True,
            text=True,
            timeout=10
        )


        for line in result.stdout.splitlines():

            if "|" not in line:
                continue

            name, app_id = line.split(
                "|",
                1
            )

            name = name.strip()
            app_id = app_id.strip()

            if name and app_id:

                apps[
                    name.lower()
                ] = (
                    name,
                    app_id
                )


    except Exception as error:

        print(
            "Application discovery error:",
            error
        )


    return apps


# ============================================================
# CLEAN APPLICATION REQUEST
# ============================================================

def clean_app_request(command):

    command = command.lower().strip()

    remove_words = [
        "open",
        "launch",
        "start",
        "run",
        "please",
        "the",
        "application",
        "app",
        "for",
        "me"
    ]

    words = command.split()

    cleaned = []

    for word in words:

        if word not in remove_words:

            cleaned.append(
                word
            )

    return " ".join(
        cleaned
    ).strip()


# ============================================================
# SPECIAL WINDOWS FOLDERS
# ============================================================

def open_special_folder(command):

    command = command.lower()

    cleaned = clean_app_request(
        command
    )


    folders = {

        "downloads": "Downloads",
        "download": "Downloads",

        "documents": "Documents",
        "document": "Documents",

        "desktop": "Desktop",

        "pictures": "Pictures",
        "photos": "Pictures",

        "videos": "Videos",

        "music": "Music"
    }


    if cleaned not in folders:

        return False


    folder_name = folders[
        cleaned
    ]


    folder_path = os.path.join(
        os.path.expanduser("~"),
        folder_name
    )


    speak(
        f"Opening {folder_name}."
    )


    try:

        os.startfile(
            folder_path
        )

    except Exception as error:

        print(
            "Folder error:",
            error
        )

        speak(
            "I couldn't open that folder."
        )


    return True


# ============================================================
# OPEN WINDOWS APPLICATION
# ============================================================

def launch_installed_app(command):

    if open_special_folder(
        command
    ):

        return True


    apps = get_installed_apps()


    if not apps:

        return False


    requested = clean_app_request(
        command
    )


    if not requested:

        return False


    aliases = {

        "calc": "calculator",
        "calculator": "calculator",

        "chrome": "google chrome",
        "google chrome": "google chrome",

        "edge": "microsoft edge",

        "spotify": "spotify",

        "vlc": "vlc media player",

        "word": "word",
        "excel": "excel",
        "powerpoint": "powerpoint",

        "notepad": "notepad",

        "camera": "camera",

        "photos": "photos",

        "settings": "settings",

        "store": "microsoft store",

        "teams": "microsoft teams"
    }


    target = aliases.get(
        requested,
        requested
    )


    # --------------------------------------------------------
    # EXACT
    # --------------------------------------------------------

    if target in apps:

        display_name, app_id = apps[
            target
        ]

        speak(
            f"Opening {display_name}."
        )

        try:

            subprocess.Popen(
                [
                    "explorer.exe",
                    f"shell:AppsFolder\\{app_id}"
                ]
            )

        except Exception as error:

            print(
                "Application error:",
                error
            )

            speak(
                "I couldn't open that application."
            )

        return True


    # --------------------------------------------------------
    # CONTAINS
    # --------------------------------------------------------

    for app_name, (
        display_name,
        app_id
    ) in apps.items():

        if target in app_name:

            speak(
                f"Opening {display_name}."
            )

            try:

                subprocess.Popen(
                    [
                        "explorer.exe",
                        f"shell:AppsFolder\\{app_id}"
                    ]
                )

            except Exception as error:

                print(
                    "Application error:",
                    error
                )

                speak(
                    "I couldn't open that application."
                )

            return True


    # --------------------------------------------------------
    # FUZZY
    # --------------------------------------------------------

    matches = difflib.get_close_matches(
        requested,
        list(apps.keys()),
        n=1,
        cutoff=0.65
    )


    if matches:

        matched_name = matches[0]

        display_name, app_id = apps[
            matched_name
        ]

        speak(
            f"Opening {display_name}."
        )

        try:

            subprocess.Popen(
                [
                    "explorer.exe",
                    f"shell:AppsFolder\\{app_id}"
                ]
            )

        except Exception as error:

            print(
                "Application error:",
                error
            )

            speak(
                "I couldn't open that application."
            )

        return True


    return False


# ============================================================
# WEBSITE COMMANDS
# ============================================================

def open_website(command):

    command = command.lower()


    if "youtube" in command:

        speak(
            "Opening YouTube."
        )

        subprocess.Popen(
            [
                "cmd",
                "/c",
                "start",
                "",
                "https://www.youtube.com"
            ]
        )

        return True


    if (
        "google" in command
        and "chrome" not in command
    ):

        speak(
            "Opening Google."
        )

        subprocess.Popen(
            [
                "cmd",
                "/c",
                "start",
                "",
                "https://www.google.com"
            ]
        )

        return True


    if "chatgpt" in command:

        speak(
            "Opening ChatGPT."
        )

        subprocess.Popen(
            [
                "cmd",
                "/c",
                "start",
                "",
                "https://chatgpt.com"
            ]
        )

        return True


    if "gmail" in command:

        speak(
            "Opening Gmail."
        )

        subprocess.Popen(
            [
                "cmd",
                "/c",
                "start",
                "",
                "https://mail.google.com"
            ]
        )

        return True


    return False


# ============================================================
# SPOTIFY
# ============================================================

def spotify_control(command):

    command = command.lower().strip()


    # --------------------------------------------------------
    # OPEN SPOTIFY
    # --------------------------------------------------------

    if (
        "open spotify" in command
        or "launch spotify" in command
        or "start spotify" in command
    ):

        apps = get_installed_apps()

        spotify = apps.get(
            "spotify"
        )


        if spotify:

            display_name, app_id = spotify

            speak(
                "Opening Spotify."
            )

            subprocess.Popen(
                [
                    "explorer.exe",
                    f"shell:AppsFolder\\{app_id}"
                ]
            )

        else:

            speak(
                "I couldn't find Spotify."
            )

        return True


    # --------------------------------------------------------
    # NEXT SONG
    # --------------------------------------------------------

    if (
        "next song" in command
        or "next track" in command
        or command == "next"
        or "skip song" in command
        or "skip track" in command
    ):

        keyboard.press_and_release(
            "next track"
        )

        return True


    # --------------------------------------------------------
    # PREVIOUS SONG
    # --------------------------------------------------------

    if (
        "previous song" in command
        or "previous track" in command
        or "last song" in command
    ):

        keyboard.press_and_release(
            "previous track"
        )

        return True


    # --------------------------------------------------------
    # PAUSE
    # --------------------------------------------------------

    if (
        command == "pause"
        or "pause spotify" in command
        or "pause music" in command
    ):

        keyboard.press_and_release(
            "play/pause media"
        )

        return True


    # --------------------------------------------------------
    # PLAY
    # --------------------------------------------------------

    if (
        command == "play"
        or "play spotify" in command
        or "play music" in command
        or "resume spotify" in command
        or "resume music" in command
    ):

        keyboard.press_and_release(
            "play/pause media"
        )

        return True


    # --------------------------------------------------------
    # VOLUME UP
    # --------------------------------------------------------

    if (
        "volume up" in command
        or "increase volume" in command
        or "turn volume up" in command
    ):

        for _ in range(3):

            keyboard.press_and_release(
                "volume up"
            )

        return True


    # --------------------------------------------------------
    # VOLUME DOWN
    # --------------------------------------------------------

    if (
        "volume down" in command
        or "decrease volume" in command
        or "turn volume down" in command
    ):

        for _ in range(3):

            keyboard.press_and_release(
                "volume down"
            )

        return True


    # --------------------------------------------------------
    # MUTE
    # --------------------------------------------------------

    if (
        command == "mute"
        or "mute spotify" in command
    ):

        keyboard.press_and_release(
            "volume mute"
        )

        return True


    return False


# ============================================================
# COMPUTER CONTROLS
# ============================================================

def computer_control(command):

    command = command.lower().strip()


    # --------------------------------------------------------
    # EXIT / CLOSE APPLICATION
    # --------------------------------------------------------

    if (
        command.startswith("exit ")
        or command.startswith("close ")
    ):

        app_name = command


        if app_name.startswith("exit "):

            app_name = app_name[
                len("exit "):
            ]

        elif app_name.startswith("close "):

            app_name = app_name[
                len("close "):
            ]


        app_name = app_name.strip()


        if not app_name:

            speak(
                "Tell me which application you want me to close."
            )

            return True


        process_names = {

            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",

            "edge": "msedge.exe",
            "microsoft edge": "msedge.exe",

            "spotify": "Spotify.exe",

            "vlc": "vlc.exe",

            "notepad": "notepad.exe",

            "word": "WINWORD.EXE",

            "excel": "EXCEL.EXE",

            "powerpoint": "POWERPNT.EXE",

            "calculator": "CalculatorApp.exe"
        }


        process = process_names.get(
            app_name
        )


        if process:

            try:

                result = subprocess.run(
                    [
                        "taskkill",
                        "/IM",
                        process,
                        "/F"
                    ],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )


                if result.returncode == 0:

                    speak(
                        f"Closing {app_name}."
                    )

                else:

                    speak(
                        f"{app_name} is not currently open."
                    )

            except Exception as error:

                print(
                    "Close application error:",
                    error
                )

                speak(
                    f"I couldn't close {app_name}."
                )

            return True


        speak(
            f"I don't have a close command for {app_name} yet."
        )

        return True


    # --------------------------------------------------------
    # RESTART COMPUTER
    # --------------------------------------------------------

    if (
        "restart computer" in command
        or "restart the computer" in command
        or command == "restart"
        or "reboot computer" in command
        or "reboot the computer" in command
    ):

        speak(
            "Restarting the computer."
        )

        time.sleep(
            1
        )

        subprocess.Popen(
            [
                "shutdown",
                "/r",
                "/t",
                "0"
            ]
        )

        return True


    # --------------------------------------------------------
    # POWER OFF / SHUT DOWN COMPUTER
    # --------------------------------------------------------

    if (
        "power off computer" in command
        or "power off the computer" in command
        or "shut down computer" in command
        or "shut down the computer" in command
        or "shutdown computer" in command
        or "shutdown the computer" in command
        or command == "power off"
        or command == "shutdown"
    ):

        speak(
            "Shutting down the computer."
        )

        time.sleep(
            1
        )

        subprocess.Popen(
            [
                "shutdown",
                "/s",
                "/t",
                "0"
            ]
        )

        return True


    # --------------------------------------------------------
    # LOCK COMPUTER
    # --------------------------------------------------------

    if (
        command == "lock"
        or command == "lock computer"
        or command == "lock the computer"
        or "lock my computer" in command
    ):

        speak(
            "Locking the computer."
        )

        time.sleep(
            1
        )

        subprocess.Popen(
            [
                "rundll32.exe",
                "user32.dll,LockWorkStation"
            ]
        )

        return True


    # --------------------------------------------------------
    # SCREENSHOT
    # --------------------------------------------------------

    if (
        command == "screenshot"
        or command == "take screenshot"
        or command == "take a screenshot"
        or command == "take a screen shot"
        or command == "take a screen capture"
    ):

        try:

            speak(
                "Opening the screenshot tool."
            )

            subprocess.Popen(
                [
                    "explorer.exe",
                    "ms-screenclip:"
                ]
            )

        except Exception as error:

            print(
                "Screenshot error:",
                error
            )

            speak(
                "I couldn't open the screenshot tool."
            )

        return True


    return False


# ============================================================
# WEATHER
# ============================================================

def get_weather(command):

    try:

        location = command.lower()


        phrases = [
            "what's the weather in",
            "what is the weather in",
            "what's weather in",
            "weather in",
            "weather at"
        ]


        for phrase in phrases:

            if phrase in location:

                location = location.split(
                    phrase,
                    1
                )[1].strip()

                break


        if not location:

            speak(
                "Tell me the city you want the weather for."
            )

            return True


        response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": location,
                "count": 5,
                "language": "en",
                "format": "json"
            },
            timeout=10
        )


        response.raise_for_status()

        data = response.json()

        results = data.get(
            "results",
            []
        )


        if not results:

            speak(
                f"I couldn't find {location}."
            )

            return True


        place = results[0]


        latitude = place[
            "latitude"
        ]

        longitude = place[
            "longitude"
        ]

        city = place.get(
            "name",
            location
        )


        weather = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "apparent_temperature,"
                    "wind_speed_10m"
                ),
                "timezone": "auto"
            },
            timeout=10
        )


        weather.raise_for_status()

        current = weather.json().get(
            "current",
            {}
        )


        temperature = current.get(
            "temperature_2m"
        )

        feels_like = current.get(
            "apparent_temperature"
        )

        humidity = current.get(
            "relative_humidity_2m"
        )

        wind = current.get(
            "wind_speed_10m"
        )


        speak(
            f"In {city}, it is "
            f"{temperature} degrees Celsius. "
            f"It feels like {feels_like} degrees. "
            f"Humidity is {humidity} percent, "
            f"with winds around "
            f"{wind} kilometres per hour."
        )


        return True


    except Exception as error:

        print(
            "Weather error:",
            error
        )

        speak(
            "I couldn't retrieve the weather right now."
        )

        return True


# ============================================================
# BATTERY
# ============================================================

def battery_status():

    try:

        battery = psutil.sensors_battery()


        if battery is None:

            speak(
                "I can't access the battery information."
            )

            return True


        percent = round(
            battery.percent
        )


        if battery.power_plugged:

            speak(
                f"Your battery is at {percent} percent "
                f"and the laptop is charging."
            )

        else:

            speak(
                f"Your battery is at {percent} percent."
            )


    except Exception as error:

        print(
            "Battery error:",
            error
        )

        speak(
            "I couldn't check the battery."
        )


    return True


# ============================================================
# TIME
# ============================================================

def tell_time():

    current_time = datetime.now().strftime(
        "%I:%M %p"
    )

    speak(
        f"The time is {current_time}."
    )


# ============================================================
# RECORD WHILE SPACE IS HELD
# ============================================================

def record_while_holding_space():

    print()
    print(
        "Listening..."
    )

    update_window(
        "LISTENING..."
    )


    audio = pyaudio.PyAudio()

    stream = None

    frames = []


    try:

        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )


        while (
            running
            and space_pressed
        ):

            data = stream.read(
                1024,
                exception_on_overflow=False
            )

            frames.append(
                data
            )


    except Exception as error:

        print(
            "Recording error:",
            error
        )

        return None


    finally:

        if stream is not None:

            try:

                stream.stop_stream()
                stream.close()

            except:
                pass


        audio.terminate()


    if not frames:

        return None


    raw_audio = b"".join(
        frames
    )


    return sr.AudioData(
        raw_audio,
        16000,
        2
    )


# ============================================================
# PROCESS COMMAND
# ============================================================

def process_command(command):

    command_lower = command.lower().strip()


    # ========================================================
    # SHUTDOWN CURSIX
    # ========================================================

    if command_lower in [
        "stop cursix",
        "shutdown cursix",
        "shut down cursix",
        "goodbye cursix",
        "close cursix",
        "exit cursix"
    ]:

        shutdown_cursix()

        return False


    # ========================================================
    # SPOTIFY
    # ========================================================

    if spotify_control(
        command_lower
    ):

        return True


    # ========================================================
    # COMPUTER CONTROLS
    # ========================================================

    if computer_control(
        command_lower
    ):

        return True


    # ========================================================
    # TIME
    # ========================================================

    if (
        "what time" in command_lower
        or "time is it" in command_lower
        or "current time" in command_lower
        or "what's the time" in command_lower
    ):

        tell_time()

        return True


    # ========================================================
    # BATTERY
    # ========================================================

    if (
        "battery" in command_lower
        or "battery level" in command_lower
        or "battery percentage" in command_lower
        or "how much battery" in command_lower
    ):

        battery_status()

        return True


    # ========================================================
    # WEATHER
    # ========================================================

    if "weather" in command_lower:

        get_weather(
            command_lower
        )

        return True


    # ========================================================
    # WEBSITES
    # ========================================================

    if open_website(
        command_lower
    ):

        return True


    # ========================================================
    # WINDOWS APPS
    # ========================================================

    if (
        "open " in command_lower
        or "launch " in command_lower
        or "start " in command_lower
    ):

        if launch_installed_app(
            command_lower
        ):

            return True


        speak(
            "I couldn't find that application."
        )

        return True


    # ========================================================
    # UNKNOWN
    # ========================================================

    speak(
        "I'm still learning that command."
    )

    return True


# ============================================================
# VOICE WORKER
# ============================================================

def voice_worker():

    global running


    print()
    print(
        "Ready. Hold SPACE to speak."
    )


    while running:

        try:

            # ------------------------------------------------
            # WAIT FOR SPACE
            # ------------------------------------------------

            while (
                running
                and not space_pressed
            ):

                time.sleep(
                    0.03
                )


            if not running:

                break


            # ------------------------------------------------
            # RECORD
            # ------------------------------------------------

            audio_data = record_while_holding_space()


            if audio_data is None:

                continue


            print(
                "Processing..."
            )

            update_window(
                "PROCESSING..."
            )


            # ------------------------------------------------
            # SPEECH RECOGNITION
            # ------------------------------------------------

            try:

                command = recognizer.recognize_google(
                    audio_data
                )


                print(
                    "You said:",
                    command
                )


                process_command(
                    command
                )


            except sr.UnknownValueError:

                speak(
                    "Sorry, I didn't understand."
                )


            except sr.RequestError:

                speak(
                    "The speech recognition service "
                    "is unavailable right now."
                )


            except Exception as error:

                print(
                    "Command error:",
                    error
                )

                speak(
                    "I had trouble processing that command."
                )


            if running:

                print()
                print(
                    "Ready. Hold SPACE to speak."
                )

                update_window(
                    "READY"
                )


        except Exception as error:

            if running:

                print(
                    "Voice worker error:",
                    error
                )

                time.sleep(
                    0.2
                )


# ============================================================
# SPEECH RECOGNIZER
# ============================================================

recognizer = sr.Recognizer()

recognizer.energy_threshold = 400

recognizer.dynamic_energy_threshold = True

recognizer.pause_threshold = 0.6


# ============================================================
# START
# ============================================================

print()
print(
    "Loading Cursix..."
)
print()


# ============================================================
# CREATE WINDOW
# ============================================================

create_window()


# ============================================================
# CAPTURE SPACEBAR
# ============================================================

keyboard.on_press_key(
    "space",
    space_down,
    suppress=True
)

keyboard.on_release_key(
    "space",
    space_up,
    suppress=True
)


# ============================================================
# CTRL + C
# ============================================================

keyboard.add_hotkey(
    "ctrl+c",
    shutdown_cursix
)


# ============================================================
# START VOICE WORKER
# ============================================================

worker = threading.Thread(
    target=voice_worker,
    daemon=True
)

worker.start()


# ============================================================
# STARTUP VOICE
# ============================================================

speak_async(
    "Cursix is ready, Brilliant."
)


# ============================================================
# WINDOW LOOP
# ============================================================

try:

    window.mainloop()

except KeyboardInterrupt:

    shutdown_cursix()

finally:

    running = False

    try:

        keyboard.unhook_all()

    except:

        pass

    print(
        "Cursix has stopped."
    )