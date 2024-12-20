from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from openai import OpenAI
import os

app = FastAPI()

client = OpenAI()
templates = Jinja2Templates(directory="templates")  # If you need templating for advanced rendering

# Define the input schema
class TTSRequest(BaseModel):
    text: str
    voice: str = "alloy"  # Default voice can be overridden
    model: str = "tts-1"  # Default model can be overridden

@app.post("/process-tts/")
async def process_tts(input: TTSRequest):
    """
    Endpoint to process text-to-speech using OpenAI API.
    Returns the generated TTS audio file and a playback link.
    """
    try:
        # Use the OpenAI API to create a TTS response
        response = client.audio.speech.create(
            model=input.model,
            voice=input.voice,
            input=input.text
        )
        
        # Save the audio output to a file
        file_path = "output.mp3"
        response.stream_to_file(file_path)
        
        # Return JSON response with playback URL
        playback_url = f"http://127.0.0.1:8000/play-audio/{os.path.basename(file_path)}"
        return JSONResponse(content={"message": "TTS processed successfully", "playback_url": playback_url})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing TTS: {str(e)}")


@app.get("/play-audio/{filename}")
async def play_audio(filename: str):
    """
    Serve the audio file for playback in Swagger UI.
    """
    file_path = os.path.join(os.getcwd(), filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg")
    else:
        raise HTTPException(status_code=404, detail="Audio file not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
