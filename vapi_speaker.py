import os
import requests
from playsound import playsound

VAPI_API_KEY = os.environ.get("VAPI_API_KEY", "YOUR_VAPI_API_KEY")  # Replace with your actual key or set as env var
VAPI_TTS_ENDPOINT = "https://api.vapi.ai/tts"  # Placeholder, update if needed
VAPI_VOICE = "en-US-Wavenet-D"  # Replace with your preferred voice

SUMMARY_FILE = "read.txt"
RECORD_FILE = "record.txt"
AUDIO_FILE = "vapi_summary.mp3"

def speak_summary(summary_path=SUMMARY_FILE):
    if not os.path.exists(summary_path):
        print(f"No summary file found at {summary_path}")
        return
    with open(summary_path, "r") as f:
        summary_text = f.read().strip()
    if not summary_text:
        print("Summary file is empty.")
        return
    print("Sending summary to Vapi TTS API...")
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": summary_text,
        "voice": VAPI_VOICE
    }
    response = requests.post(VAPI_TTS_ENDPOINT, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"Vapi TTS API error: {response.status_code} {response.text}")
        return
    # Assume the API returns a direct audio file or a URL to download
    if "audio_url" in response.json():
        audio_url = response.json()["audio_url"]
        audio_data = requests.get(audio_url).content
    else:
        audio_data = response.content
    with open(AUDIO_FILE, "wb") as f:
        f.write(audio_data)
    print("Playing summary audio...")
    playsound(AUDIO_FILE)
    # Clean up
    os.remove(AUDIO_FILE)
    if os.path.exists(SUMMARY_FILE):
        os.remove(SUMMARY_FILE)
    if os.path.exists(RECORD_FILE):
        os.remove(RECORD_FILE)
    print("Summary and record files wiped.") 