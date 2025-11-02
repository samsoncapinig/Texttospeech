"""
Streamlit Text-to-Speech App using Microsoft Edge TTS
File: streamlit_edge_tts_app.py

This single-file repository contains a Streamlit app that converts input text to
natural-sounding English speech using Microsoft Neural voices via the `edge-tts` package.

Features
- Choose from a selection of natural male and female English neural voices.
- Live controls for speaking rate and volume (via SSML prosody attributes).
- Play audio in the browser and download the generated MP3.
- Small, single-file app ready to upload to GitHub and run with Streamlit.

Requirements (put into requirements.txt in your repo):
streamlit>=1.20
edge-tts>=2.0.0

Note on Edge TTS
- The `edge-tts` Python package calls Microsoft Text-to-Speech endpoints under the hood and
  streams neural voices. The package is widely used and supports many high-quality neural
  voices (US/UK/AU/CA English, etc.). Network access is required to synthesize audio.

How to run
1. Create a virtualenv (recommended) and install requirements:
   python -m venv .venv
   source .venv/bin/activate   # Linux / macOS
   .venv\Scripts\activate     # Windows
   pip install -r requirements.txt

2. Run the Streamlit app:
   streamlit run streamlit_edge_tts_app.py

3. Open the URL shown by Streamlit (usually http://localhost:8501).

License: MIT (feel free to reuse)

"""

import streamlit as st
import tempfile
import asyncio
import os
from pathlib import Path
import edge_tts

# -----------------------------
# Helper: Synthesize with edge-tts
# -----------------------------
async def synthesize_to_file_async(text: str, voice: str, rate: str = "0%", volume: str = "0dB", output_path: str = "output.mp3"):
    """
    Use edge-tts to synthesize `text` with the given `voice`.
    rate: e.g. "+0%", "-10%", "0%"
    volume: e.g. "0dB", "-3dB", "+3dB"
    Saves MP3 to output_path.
    """
    # Build SSML wrapper to allow rate and volume control
    ssml = f"""<speak><prosody rate=\"{rate}\" volume=\"{volume}\">{escape_xml(text)}</prosody></speak>"""

    communicate = edge_tts.Communicate(ssml, voice)
    # edge-tts Communicate.save writes the audio to a file path
    await communicate.save(output_path)
    return output_path


def synthesize_to_file(text: str, voice: str, rate: str = "0%", volume: str = "0dB", output_path: str = None):
    """
    Synchronous wrapper for Streamlit usage.
    Returns bytes of the mp3 file.
    """
    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        output_path = tmp.name
        tmp.close()

    # Run async synth
    asyncio.run(synthesize_to_file_async(text, voice, rate, volume, output_path))

    with open(output_path, "rb") as f:
        data = f.read()
    try:
        os.remove(output_path)
    except Exception:
        pass
    return data


# Minimal escaping for XML used inside SSML
def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
    )


# -----------------------------
# Voice lists (male/female suggestions)
# -----------------------------
# edge-tts supports many voices. Below are some commonly available Neural voices.
# You can extend this list or let users type a voice name directly.
MALE_VOICES = [
    "en-US-GuyNeural",
    "en-US-AriaNeural",  # Aria is female but included for variety in default
    "en-GB-RyanNeural",
    "en-AU-WilliamNeural",
    "en-CA-LiamNeural",
]

FEMALE_VOICES = [
    "en-US-JennyNeural",
    "en-US-AmberNeural",
    "en-GB-LibbyNeural",
    "en-AU-SallyNeural",
    "en-CA-ClaraNeural",
]

ALL_VOICES = sorted(set(MALE_VOICES + FEMALE_VOICES))


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Natural TTS (Edge-TTS) — Streamlit", page_icon=":microphone:")
st.title("Natural English Text→Speech (Edge-TTS)")
st.markdown(
    """
    Simple Streamlit app to synthesize natural-sounding English speech.

    Choose a voice, enter text, and click **Convert**. You can then play the audio or download it.
    """
)

# Layout
col1, col2 = st.columns([3, 1])

with col1:
    text_input = st.text_area("Enter text to speak", value="Hello — this is a sample of natural-sounding English speech.", height=180)

with col2:
    gender = st.radio("Voice gender", options=["Female", "Male", "Show all"], index=0)
    if gender == "Female":
        voice = st.selectbox("Select voice", FEMALE_VOICES, index=0)
    elif gender == "Male":
        voice = st.selectbox("Select voice", MALE_VOICES, index=0)
    else:
        voice = st.selectbox("Select voice", ALL_VOICES, index=0)

    rate_pct = st.slider("Speaking rate (percent)", min_value=-50, max_value=50, value=0, step=5)
    # Map slider numeric to SSML percent string
    rate_str = f"{rate_pct}%"

    volume_db = st.slider("Volume (dB)", min_value=-10, max_value=10, value=0, step=1)
    volume_str = f"{volume_db}dB"

    st.write("Voice preview:", voice)

# Controls: Convert button
convert = st.button("Convert to speech")

if convert:
    if not text_input.strip():
        st.error("Please enter some text to synthesize.")
    else:
        try:
            with st.spinner("Synthesizing — contacting Edge TTS..."):
                mp3_bytes = synthesize_to_file(text_input, voice, rate_str, volume_str)

            st.success("Synthesis complete — play below")

            # Play audio
            st.audio(mp3_bytes)

            # Download button
            st.download_button(
                label="Download MP3",
                data=mp3_bytes,
                file_name="speech.mp3",
                mime="audio/mpeg",
            )

        except Exception as e:
            st.exception(e)

# Helpful notes / tips
st.markdown("---")
st.subheader("Tips and notes")
st.markdown(
    """
    - If you see network errors, check that your environment has internet access. `edge-tts` needs to reach Microsoft's speech endpoints.
    - To see the full list of supported voices, install `edge-tts` and run: `python -m edge_tts --list-voices` from your shell.
    - For long-form text consider batching into smaller paragraphs to avoid timeouts.
    """
)

# Small debug / advanced section (collapsible)
with st.expander("Advanced / Debug"):
    st.write("Edge-tts is installed version:")
    try:
        import pkg_resources
        ver = pkg_resources.get_distribution("edge-tts").version
        st.write(ver)
    except Exception:
        st.write("edge-tts not installed or cannot detect version")
    st.write("Selected voice:", voice)
    st.write("Rate (SSML):", rate_str)
    st.write("Volume (SSML):", volume_str)


# EOF
