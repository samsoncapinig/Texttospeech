import streamlit as st
from google.cloud import texttospeech
from io import BytesIO
from gtts import gTTS
import os

st.title("🌐 Text to Speech Converter (Filipino + English)")
st.write("Convert text into natural voices online!")

# ---- GOOGLE CLOUD CREDENTIALS ----
# You must have a service-account JSON key from Google Cloud.
# In Streamlit Cloud → Settings → Secrets → add:
# [google]
# credentials = <paste the JSON key here>
if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ and "google" in st.secrets:
    creds_file = "/tmp/google_key.json"
    with open(creds_file, "w") as f:
        f.write(st.secrets["google"]["credentials"])
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_file

# ---- Voice Selection ----
voice_choice = st.selectbox(
    "Choose a voice:",
    [
        "Filipino (Default)",
        "English - Male (John)",
        "English - Male (Matthew)",
        "English - Female (Joanna)",
        "English - Female (Aria)",
    ],
)

# ---- Text Input ----
text = st.text_area("Enter your text:", "")

# ---- Convert Button ----
if st.button("Convert to Speech"):
    if text.strip() == "":
        st.warning("⚠️ Please enter some text first.")
    else:
        audio_bytes = BytesIO()

        if voice_choice == "Filipino (Default)":
            # Use gTTS for Filipino
            tts = gTTS(text, lang="tl")
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)
        else:
            # Use Google Cloud TTS for English
            voice_map = {
                "English - Male (John)": "en-US-JohnNeural",
                "English - Male (Matthew)": "en-US-Standard-B",
                "English - Female (Joanna)": "en-US-Standard-A",
                "English - Female (Aria)": "en-US-Neural2-C",
            }

            voice_name = voice_map[voice_choice]
            client = texttospeech.TextToSpeechClient()

            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name=voice_name,
            )
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

            try:
                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config,
                )
                audio_bytes.write(response.audio_content)
                audio_bytes.seek(0)
            except Exception as e:
                st.error(f"Google TTS Error: {e}")

        if audio_bytes.getbuffer().nbytes > 0:
            st.success("✅ Speech generated successfully!")
            st.audio(audio_bytes, format="audio/mp3")
            st.download_button("Download MP3", audio_bytes, file_name="speech.mp3")
