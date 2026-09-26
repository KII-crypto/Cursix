import openwakeword

print("Cursix wake-word system is loading...")

try:
    openwakeword.utils.download_models()
    print("Wake-word models downloaded successfully!")
except Exception as e:
    print("Error:", e)

print("Wake-word system test finished.")