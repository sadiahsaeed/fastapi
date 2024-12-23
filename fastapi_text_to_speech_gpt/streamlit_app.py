import streamlit as st
import requests
import os

# Streamlit app
def main():
    st.title("Text-to-Speech (TTS) Demo")

    # Input fields
    text = st.text_area("Enter text to convert to speech:", height=120)
    voice_options = ["echo", "alloy", "fable", "onyx", "nova", "shimmer"]
    selected_voice = st.selectbox("Select voice:", voice_options, index=0)
    
    model_options = ["tts-1", "tts-1-hd"]
    selected_model = st.selectbox("Select model:", model_options, index=0)
    
    # Button to trigger TTS
    if st.button("Convert to Speech"):
        if not text.strip():
            st.error("Please enter some text.")
            return

        # Prepare request payload
        payload = {
            "text": text,
            "voice": selected_voice,
            "model": selected_model
        }

        try:
            # Send POST request to FastAPI endpoint
            response = requests.post("http://127.0.0.1:8000/process-tts/", json=payload)
            
            if response.status_code == 200:
                # Parse the JSON response
                data = response.json()
                file_path = data.get("file_path")
                
                if file_path and os.path.exists(file_path):
                    st.success("TTS processing completed!")
                    
                    # Display an audio player in Streamlit
                    with open(file_path, "rb") as audio_file:
                        st.audio(audio_file.read(), format="audio/mp3")
                else:
                    st.error("File path not found or file does not exist.")
            else:
                # Error from the FastAPI endpoint
                st.error(f"Error: {response.json()['detail']}")
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
