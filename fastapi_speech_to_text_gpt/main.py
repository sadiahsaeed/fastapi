from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from openai import OpenAI
import shutil
import os

app = FastAPI()

client = OpenAI()

# Directory to temporarily store uploaded audio files
UPLOAD_DIR = "uploaded_audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Acceptable audio MIME types
ACCEPTABLE_AUDIO_TYPES = [
    "audio/mpeg",  # mp3
    "audio/mp4",   # mp4
    "audio/x-m4a", # m4a
    "audio/mpg",   # mpga
    "audio/wav",   # wav
    "audio/webm"   # webm
]

@app.post("/transcribe-audio/")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Endpoint to transcribe audio to text using OpenAI's Whisper API.
    Accepts an audio file from the user, validates its type, and returns the transcription.
    """
    # Validate audio file type
    if file.content_type not in ACCEPTABLE_AUDIO_TYPES:
        return JSONResponse(
            content={"error": f"Invalid file type: {file.content_type}. Only audio files are allowed."},
            status_code=400
        )

    try:
        # Save the uploaded file to the server
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Open the saved file for transcription
        with open(file_path, "rb") as audio_file:
            transcription = client.audio.translations.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        
        # Clean up the uploaded file
        os.remove(file_path)
        
        return JSONResponse(content={"transcription": transcription})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing transcription: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
