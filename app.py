import streamlit as st
from gtts import gTTS
from io import BytesIO
import asyncio
import edge_tts

st.title("Text to Speech Converter 🇵🇭🇺🇸")
st.write("Enter text below and convert it to Filipino or English speech!")

# Voice selection
voice_choice = st.selectbox(
    "Choose a voice:",
    [
        "Filipino (Default)",
        "English - Male (Ryan)",
        "English - Male (Eric)",
        "English - Male (Guy)",
        "English - Female (Jenny)",
        "English - Female (Aria)"
    ]
)

# Text input
text = st.text_area("Enter your text:", "")

# Convert button
if st.button("Convert to Speech"):
    if text.strip() == "":
        st.warning("Please enter some text first.")
    else:
        audio_bytes = BytesIO()

        if voice_choice == "Filipino (Default)":
            # Use gTTS for Filipino
            tts = gTTS(text, lang='tl')
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)

        else:
            # Use Microsoft Edge-TTS for English voices
            voice_map = {
                "English - Male (Ryan)": "en-US-RyanNeural",
                "English - Male (Eric)": "en-US-EricNeural",
                "English - Male (Guy)": "en-US-GuyNeural",
                "English - Female (Jenny)": "en-US-JennyNeural",
                "English - Female (Aria)": "en-US-AriaNeural",
            }

            voice = voice_map[voice_choice]

            async def synthesize():
                tts = edge_tts.Communicate(text, voice)
                with BytesIO() as f:
                    async for chunk in tts.stream():
                        if chunk["type"] == "audio":
                            f.write(chunk["data"])
                    f.seek(0)
                    audio_bytes.write(f.read())

            asyncio.run(synthesize())
            audio_bytes.seek(0)

        st.success("✅ Speech generated successfully!")
        st.audio(audio_bytes, format="audio/mp3")
        st.download_button("Download MP3", audio_bytes, file_name="speech.mp3")
