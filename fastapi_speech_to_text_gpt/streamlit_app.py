import streamlit as st
import requests

# Set the FastAPI endpoint URL
API_URL = "http://localhost:8000/transcribe-audio/"

def main():
    st.title("Audio Transcription App")

    st.write("""
    Upload an audio file (mp3, mp4, m4a, mpga, wav, webm) and click **Transcribe** 
    to get a transcription using OpenAI's Whisper model.
    """)

    # File uploader for the audio file
    audio_file = st.file_uploader("Upload your audio file here", type=["mp3", "mp4", "m4a", "mpga", "wav", "webm"])
    
    if audio_file is not None:
        st.write(f"File uploaded: **{audio_file.name}**")
        
        # Button to trigger transcription
        if st.button("Transcribe"):
            # Show a spinner while processing
            with st.spinner("Transcribing..."):
                try:
                    # Convert the file to a format suitable for requests
                    files = {
                        "file": (audio_file.name, audio_file, audio_file.type)
                    }
                    
                    # Make a POST request to the FastAPI endpoint
                    response = requests.post(API_URL, files=files)
                    
                    # Raise an exception if the request was not successful
                    response.raise_for_status()
                    
                    # Extract the transcription from the response
                    result = response.json()
                    
                    if "transcription" in result:
                        st.success("Transcription Successful!")
                        st.write("**Transcription:**")
                        st.write(result["transcription"])
                    else:
                        st.error("No transcription found in the response.")
                
                except requests.exceptions.RequestException as e:
                    st.error(f"Error calling API: {e}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
