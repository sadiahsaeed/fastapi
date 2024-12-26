import streamlit as st
import requests
import tempfile
import pyaudio
import wave
import threading
import os

# Define the FastAPI endpoints
TRANSCRIBE_ENDPOINT = "http://localhost:8000/process-query/"  # Unified endpoint

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

st.title("Live Audio Recorder and Query Processor")

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

# Transcribe and Process button
if st.button("Transcribe and Process Query"):
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
            response = requests.post(TRANSCRIBE_ENDPOINT, files=files)

        # Display the transcription and query results
        if response.status_code == 200:
            result = response.json()
            transcription = result.get("transcription", "No transcription found.")
            query_result = result.get("result", "No query response found.")
            st.success("Results:")
            st.text(f"Transcription: {transcription}")
            st.text(f"Query Response: {query_result}")
        else:
            st.error(f"Error: {response.status_code} - {response.text}")

        # Clean up temporary file
        os.remove(file_path)

# Text Query Section
st.subheader("Text Query")
text_query = st.text_input("Enter your query:")

if st.button("Submit Text Query"):
    if text_query:
        # Send the text query to the FastAPI endpoint
        with st.spinner("Processing text query..."):
            response = requests.post(TRANSCRIBE_ENDPOINT, data={"query": text_query})

        if response.status_code == 200:
            result = response.json().get("result", "No result found.")
            st.success("Query Response:")
            st.text(result)
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
    else:
        st.warning("Please enter a query.")
