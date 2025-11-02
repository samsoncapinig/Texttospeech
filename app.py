# Streamlit Audio Transcriber + Edge-TTS Voice Playback
#
# Enhancements:
# ✅ Added text-to-speech using Microsoft Edge-TTS (neural voices)
# ✅ Realistic male/female English voices (US, UK, AU, IN)
# ✅ Allows playback and download of the spoken transcript
#
# Requirements: streamlit, faster-whisper, torch, edge-tts, ffmpeg installed

import streamlit as st
from faster_whisper import WhisperModel
import tempfile
import os
from pathlib import Path
import math
import uuid
import subprocess
import asyncio
import edge_tts

st.set_page_config(page_title='Audio → Text + Neural Voices', layout='wide')

st.title('🎧 Audio → Text Transcriber with Microsoft Edge Neural Voices')
st.markdown(
    'Upload an MP3 or M4A file. The app will transcribe it with **faster-whisper**, '
    'and you can listen to the transcript using **Microsoft Edge-TTS** voices.'
)

uploaded_file = st.file_uploader('Upload audio file (MP3 or M4A)', type=['mp3', 'm4a'])

col1, col2, col3 = st.columns([1,1,1])
with col1:
    chunk_minutes = st.number_input('Chunk size (minutes)', min_value=1, max_value=60, value=10)
with col2:
    model_size = st.selectbox('Whisper model size', ['tiny', 'base', 'small', 'medium', 'large-v2'], index=2)
with col3:
    device = st.selectbox('Device', ['cpu', 'cuda'], index=0)

def run_ffmpeg(input_path, output_path, extra_args):
    cmd = ["ffmpeg", "-y", "-i", str(input_path)] + extra_args + [str(output_path)]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Async voice synthesis using Edge-TTS
async def synthesize_voice(text, voice_name, output_file):
    tts = edge_tts.Communicate(text, voice_name)
    await tts.save(output_file)

if uploaded_file is not None:
    st.info('Saving and preparing audio...')
    tmp_dir = Path(tempfile.gettempdir()) / f"st_transcribe_{uuid.uuid4().hex}"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    input_path = tmp_dir / uploaded_file.name
    with open(input_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())

    st.write(f'Uploaded: {uploaded_file.name}')

    # Convert to WAV (mono, 16kHz, 16-bit PCM)
    wav_path = tmp_dir / (input_path.stem + '.wav')
    st.write('Converting to WAV...')
    run_ffmpeg(input_path, wav_path, ["-ar", "16000", "-ac", "1", "-acodec", "pcm_s16le"])
    
    # Get duration
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", str(wav_path)]
    result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    duration_seconds = float(result.stdout.decode().strip())
    chunk_seconds = int(chunk_minutes * 60)
    num_chunks = math.ceil(duration_seconds / chunk_seconds)
    st.write(f'Splitting into {num_chunks} chunk(s)...')

    chunk_paths = []
    for i in range(num_chunks):
        start_time = i * chunk_seconds
        chunk_file = tmp_dir / f"chunk_{i:04d}.wav"
        run_ffmpeg(wav_path, chunk_file, ["-ss", str(start_time), "-t", str(chunk_seconds)])
        chunk_paths.append(str(chunk_file))

    # Load model
    st.write('Loading Whisper model...')
    try:
        model = WhisperModel(model_size, device=device, compute_type='float16' if device=='cuda' else 'int8')
    except Exception as e:
        st.error(f'Error loading model: {e}')
        st.stop()

    # Transcribe chunks
    final_transcript = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, cpath in enumerate(chunk_paths):
        status_text.info(f'Transcribing chunk {idx+1}/{len(chunk_paths)}...')
        segments, _ = model.transcribe(cpath, beam_size=5, language='en')
        chunk_text = ' '.join([s.text for s in segments])
        final_transcript.append(chunk_text.strip())
        progress_bar.progress((idx+1)/len(chunk_paths))

    status_text.success('✅ Transcription complete!')

    # Combine
    full_text = '\n\n'.join(final_transcript)

    st.subheader('📝 Transcription (English)')
    st.text_area('Transcript', value=full_text, height=400)

    st.download_button('📄 Download transcript (.txt)',
                       data=full_text,
                       file_name=f"transcript_{input_path.stem}.txt",
                       mime='text/plain')

    # --- Neural Voice Section ---
    st.markdown('---')
    st.subheader('🗣️ Listen to the Transcript (Microsoft Edge Neural Voices)')

    voice_option = st.selectbox(
        'Select a Voice',
        {
            "Female (US) - Aria": "en-US-AriaNeural",
            "Male (US) - Guy": "en-US-GuyNeural",
            "Female (UK) - Libby": "en-GB-LibbyNeural",
            "Male (UK) - Ryan": "en-GB-RyanNeural",
            "Female (Australia) - Natasha": "en-AU-NatashaNeural",
            "Male (India) - Prabhat": "en-IN-PrabhatNeural"
        }
    )

    if st.button('Generate Voice'):
        st.info('Generating natural voice... please wait.')
        voice_file = tmp_dir / "transcript_voice.mp3"
        voice_text = full_text[:4000]  # Avoid overly long input to TTS
        asyncio.run(synthesize_voice(voice_text, voice_option, voice_file))

        st.audio(str(voice_file), format='audio/mp3')
        with open(voice_file, "rb") as f:
            st.download_button('🎧 Download Voice MP3', f, file_name="transcript_voice.mp3")

    st.success('All done!')

    st.markdown('---')
    st.markdown('**Dependencies**')
    st.code('streamlit\nfaster-whisper\ntorch\nedge-tts')
