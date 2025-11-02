import streamlit as st
from gtts import gTTS
from io import BytesIO
import asyncio
import edge_tts
import aiohttp

st.title("Text to Speech Converter 🇵🇭🇺🇸")
st.write("Convert text to Filipino or English speech with natural voices!")

# Voice selection
voice_choice = st.selectbox(
    "Choose a voice:",
    [
        "Filipino (Default)",
        "English - Male (Ryan)",
        "English - Male (Eric)",
        "English - Male (Guy)",
        "English - Female (Jenny)",
        "English - Female (Aria)",
    ],
)

# Text input
text = st.text_area("Enter your text:", "")

# Convert button
if st.button("Convert to Speech"):
    if text.strip() == "":
        st.warning("⚠️ Please enter some text first.")
    else:
        audio_bytes = BytesIO()

        if voice_choice == "Filipino (Default)":
            # gTTS for Filipino
            try:
                tts = gTTS(text, lang="tl")
                tts.write_to_fp(audio_bytes)
                audio_bytes.seek(0)
            except Exception as e:
                st.error(f"Error generating Filipino speech: {e}")

        else:
            # Edge-TTS for English voices
            voice_map = {
                "English - Male (Ryan)": "en-US-RyanNeural",
                "English - Male (Eric)": "en-US-EricNeural",
                "English - Male (Guy)": "en-US-GuyNeural",
                "English - Female (Jenny)": "en-US-JennyNeural",
                "English - Female (Aria)": "en-US-AriaNeural",
            }
            voice = voice_map[voice_choice]

            async def synthesize():
                try:
                    tts = edge_tts.Communicate(text, voice)
                    async for chunk in tts.stream():
                        if chunk["type"] == "audio":
                            audio_bytes.write(chunk["data"])
                except aiohttp.ClientConnectorError:
                    st.error("❌ Unable to connect to Microsoft TTS service. Please check your internet connection.")
                except Exception as e:
                    st.error(f"⚠️ TTS Error: {str(e)}")
