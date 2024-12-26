import streamlit as st
import requests
import tempfile
import pyaudio
import wave
import threading
import os
# Define the FastAPI endpoint
FASTAPI_ENDPOINT = "http://localhost:8000/transcribe-audio/"

# Audio recording settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024

def record_audio(stop_event, frames):
    """Record audio until stop_event is set."""
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    while not stop_event.is_set():
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()

st.title("Live Audio Recorder and Transcriber")

if "recording" not in st.session_state:
    st.session_state.recording = False

if "stop_event" not in st.session_state:
    st.session_state.stop_event = threading.Event()

if "frames" not in st.session_state:
    st.session_state.frames = []

# Start button
if st.button("Start Recording"):
    if not st.session_state.recording:
        st.session_state.recording = True
        st.session_state.frames = []
        st.session_state.stop_event.clear()
        threading.Thread(target=record_audio, args=(st.session_state.stop_event, st.session_state.frames)).start()
        st.write("Recording started...")
    else:
        st.warning("Recording is already in progress.")

# Stop button
if st.button("Stop Recording"):
    if st.session_state.recording:
        st.session_state.recording = False
        st.session_state.stop_event.set()
        st.write("Recording stopped.")
    else:
        st.warning("No recording in progress.")

# Transcribe button
if st.button("Transcribe Audio"):
    if not st.session_state.frames:
        st.warning("No audio recorded to transcribe.")
    else:
        # Save recorded audio to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            file_path = temp_file.name
            with wave.open(file_path, "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b"".join(st.session_state.frames))

        # Send the file to the FastAPI endpoint
        with open(file_path, "rb") as audio_file:
            files = {"file": ("audio.wav", audio_file, "audio/wav")}
            response = requests.post(FASTAPI_ENDPOINT, files=files)

        # Display the transcription result
        if response.status_code == 200:
            transcription = response.json().get("transcription", "No transcription found.")
            st.success("Transcription:")
            st.text(transcription)
        else:
            st.error(f"Error: {response.status_code} - {response.text}")

        # Clean up temporary file
        os.remove(file_path)
