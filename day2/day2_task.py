import os
import requests

# 1. PASTE YOUR ACTUAL MURF API KEY HERE
MURF_API_KEY = "ap2_b88fc326-2d8c-4eb0-a449-44ba11946419"

def print_header():
    print("=" * 60)
    print("   🎙️  MURF AI VOICE FOR BHARAT - DAY 2 PIPELINE")
    print("=" * 60)

def download_audio(audio_url, output_filename="day2_output.mp3"):
    print(f"\n[📥 Downloading] Fetching generated audio file from Murf cloud...")
    try:
        response = requests.get(audio_url, stream=True)
        if response.status_code == 200:
            with open(output_filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            full_path = os.path.abspath(output_filename)
            print("=" * 60)
            print("  ✨ AUDIO SAVED SUCCESSFULLY TO YOUR LOCAL FOLDER! ✨")
            print(f"  📁 File Path : {full_path}")
            print(f"  🎧 File Name : {output_filename}")
            print("=" * 60)
        else:
            print(f"\n[❌ Download Failed]: Status Code {response.status_code}")
    except Exception as e:
        print(f"\n[❌ Download Error]: {e}")

def run_pipeline():
    print_header()

    if MURF_API_KEY == "YOUR_ACTUAL_MURF_API_KEY_HERE" or not MURF_API_KEY:
        print("\n[Error] Please paste your real Murf API key on line 5!\n")
        return

    # 1. Fetch valid voices
    print("[1/3] Fetching available voice library from Murf AI...")
    voices_url = "https://api.murf.ai/v1/speech/voices"
    headers = {"api-key": MURF_API_KEY}

    res = requests.get(voices_url, headers=headers)
    if res.status_code != 200:
        print(f"\n[API Error {res.status_code}]: {res.text}")
        return

    voices = res.json()
    voice_ids = [v.get("voiceId") for v in voices if "hi" in v.get("locale", "") or "IN" in v.get("locale", "")]
    selected_voice = voice_ids[0] if voice_ids else voices[0]["voiceId"]

    print(f"      ✓ Selected Voice ID: '{selected_voice}'")

    # 2. Extended Hindi Script
    big_script = (
        "नमस्कार! वॉइस फॉर भारत चैलेंज के दूसरे दिन में आपका स्वागत है। "
        "आर्टिफिशियल इंटेलिजेंस और वॉइस टेक्नोलॉजी भारत की क्षेत्रीय भाषाओं को सशक्त बना रही है। "
        "मर्फ एआई की मदद से अब हम कुछ ही सेकंड में प्राकृतिक और स्पष्ट ऑडियो तैयार कर सकते हैं। "
        "यह तकनीक डिजिटल भारत को एक नए मुकाम पर ले जाने के लिए तैयार है। धन्यवाद!"
    )

    print("\n[2/3] Synthesizing extended Hindi audio script...")
    print(f"      Text: \"{big_script[:60]}...\"")

    gen_url = "https://api.murf.ai/v1/speech/generate"
    payload = {
        "text": big_script,
        "voiceId": selected_voice,
        "format": "MP3"
    }

    gen_res = requests.post(gen_url, json=payload, headers={"api-key": MURF_API_KEY, "Content-Type": "application/json"})

    if gen_res.status_code == 200:
        audio_url = gen_res.json().get("audioFile")
        print("      ✓ Audio synthesized successfully on Murf servers!")
        
        # 3. Download locally
        print("\n[3/3] Initiating local MP3 download...")
        download_audio(audio_url, "day2_output.mp3")
    else:
        print(f"\n[Generation Error {gen_res.status_code}]: {gen_res.text}")

if __name__ == "__main__":
    run_pipeline()