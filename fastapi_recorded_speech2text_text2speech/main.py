from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import os
from openai import OpenAI

# Initialize FastAPI app
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

# CORS middleware to allow interaction with a frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend's domain for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TTSRequest(BaseModel):
    text: str
    voice: str = "echo"  #(alloy, echo, fable, onyx, nova, and shimmer)
    model: str = "tts-1"  # tts-1-hd

@app.post("/transcribe-audio/")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Endpoint to transcribe audio to text using OpenAI's Whisper API.
    """
    if file.content_type not in ACCEPTABLE_AUDIO_TYPES:
        return JSONResponse(
            content={"error": f"Invalid file type: {file.content_type}. Only audio files are allowed."},
            status_code=400
        )

    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with open(file_path, "rb") as audio_file:
            transcription = client.audio.translations.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )

        os.remove(file_path)
        return JSONResponse(content={"transcription": transcription})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing transcription: {str(e)}")

@app.post("/process-tts/")
async def process_tts(input: TTSRequest):
    """
    Endpoint to process text-to-speech using OpenAI API.
    """
    try:
        response = client.audio.speech.create(
            model=input.model,
            voice=input.voice,
            input=input.text
        )

        file_path = "output.mp3"
        response.stream_to_file(file_path)

        return {"message": "TTS processing completed", "file_path": file_path}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing TTS: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

