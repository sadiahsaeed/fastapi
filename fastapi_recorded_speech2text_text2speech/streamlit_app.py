import tempfile
import wave
import threading
import streamlit as st
import requests
import pyaudio
import os
# Streamlit app
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
FASTAPI_ENDPOINT_TRANSCRIBE = "http://localhost:8000/transcribe-audio/"
FASTAPI_ENDPOINT_TTS = "http://localhost:8000/process-tts/"

# Audio recording function
def record_audio(stop_event, frames):
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    while not stop_event.is_set():
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()

# Streamlit UI
st.title("Audio Transcription and TTS Conversion")

if "recording" not in st.session_state:
    st.session_state.recording = False

if "stop_event" not in st.session_state:
    st.session_state.stop_event = threading.Event()

if "frames" not in st.session_state:
    st.session_state.frames = []

if st.button("Start Recording"):
    if not st.session_state.recording:
        st.session_state.recording = True
        st.session_state.frames = []
        st.session_state.stop_event.clear()
        threading.Thread(target=record_audio, args=(st.session_state.stop_event, st.session_state.frames)).start()
        st.write("Recording started...")
    else:
        st.warning("Recording is already in progress.")

if st.button("Stop Recording"):
    if st.session_state.recording:
        st.session_state.recording = False
        st.session_state.stop_event.set()
        st.write("Recording stopped.")
    else:
        st.warning("No recording in progress.")

uploaded_file = st.file_uploader("Upload an audio file for transcription and TTS:", type=["wav", "mp3", "mp4", "m4a", "webm"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        file_path = temp_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())

    if st.button("Process Uploaded Audio"):
        with open(file_path, "rb") as audio_file:
            files = {"file": (uploaded_file.name, audio_file, uploaded_file.type)}
            response = requests.post(FASTAPI_ENDPOINT_TRANSCRIBE, files=files)

        os.remove(file_path)

        if response.status_code == 200:
            transcription = response.json().get("transcription", "No transcription found.")
            st.success("Transcription:")
            st.text(transcription)

            tts_payload = {
                "text": transcription,
                "voice": "echo",
                "model": "tts-1"
            }
            tts_response = requests.post(FASTAPI_ENDPOINT_TTS, json=tts_payload)

            if tts_response.status_code == 200:
                tts_data = tts_response.json()
                tts_file_path = tts_data.get("file_path")

                if tts_file_path and os.path.exists(tts_file_path):
                    with open(tts_file_path, "rb") as tts_file:
                        st.audio(tts_file.read(), format="audio/mp3")
                else:
                    st.error("TTS audio file not found.")
            else:
                st.error(f"TTS Error: {tts_response.json().get('detail', 'Unknown error.')}")
        else:
            st.error(f"Transcription Error: {response.text}")

if st.button("Transcribe and Convert to Speech"):
    if not st.session_state.frames:
        st.warning("No audio recorded to transcribe.")
    else:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            file_path = temp_file.name
            with wave.open(file_path, "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b"".join(st.session_state.frames))

        with open(file_path, "rb") as audio_file:
            files = {"file": ("audio.wav", audio_file, "audio/wav")}
            response = requests.post(FASTAPI_ENDPOINT_TRANSCRIBE, files=files)

        os.remove(file_path)

        if response.status_code == 200:
            transcription = response.json().get("transcription", "No transcription found.")
            st.success("Transcription:")
            st.text(transcription)

            tts_payload = {
                "text": transcription,
                "voice": "echo",
                "model": "tts-1"
            }
            tts_response = requests.post(FASTAPI_ENDPOINT_TTS, json=tts_payload)

            if tts_response.status_code == 200:
                tts_data = tts_response.json()
                tts_file_path = tts_data.get("file_path")

                if tts_file_path and os.path.exists(tts_file_path):
                    with open(tts_file_path, "rb") as tts_file:
                        st.audio(tts_file.read(), format="audio/mp3")
                else:
                    st.error("TTS audio file not found.")
            else:
                st.error(f"TTS Error: {tts_response.json().get('detail', 'Unknown error.')}")
        else:
            st.error(f"Transcription Error: {response.text}")
