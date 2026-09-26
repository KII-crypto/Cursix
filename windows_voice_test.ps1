Add-Type -AssemblyName System.Speech

$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer

$speaker.Volume = 100
$speaker.Rate = 0

$speaker.Speak("Hello Brilliant. This is Cursix speaking through Windows.")

$speaker.Dispose()