from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from utils import QA_Chain
from langchain_openai import OpenAIEmbeddings
import shutil
import os
import uvicorn
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize embeddings and OpenAI client
embeddings = OpenAIEmbeddings()
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

# Initialize FastAPI app
app = FastAPI()

# CORS middleware to allow interaction with a frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend's domain for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/process-query/")
async def process_query(
    query: str = Form(None),
    file: UploadFile = File(None)
):
    """
    Unified endpoint to handle queries in the form of text or audio.
    If `query` is provided, it processes the text directly.
    If `file` is provided, it transcribes the audio and processes the transcribed text.
    """
    if query:
        # Process the text query with QA_Chain
        try:
            results = QA_Chain(query=query)
            return {"result": results}
        except Exception as e:
            return JSONResponse(
                content={"error": f"Error processing query: {str(e)}"},
                status_code=500
            )

    elif file:
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

            # Process the transcribed text with QA_Chain
            try:
                results = QA_Chain(query=transcription)
                return {"result": results, "transcription": transcription}
            except Exception as e:
                return JSONResponse(
                    content={"error": f"Error processing transcribed query: {str(e)}"},
                    status_code=500
                )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing transcription: {str(e)}")

    else:
        return JSONResponse(
            content={"error": "No query or audio file provided."},
            status_code=400
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
