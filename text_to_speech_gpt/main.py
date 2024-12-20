from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

client = OpenAI()

# Define the input schema
class TTSRequest(BaseModel):
    text: str
    voice: str = "echo"  #(alloy, echo, fable, onyx, nova, and shimmer)
    model: str = "tts-1"  # tts-1-hd

@app.post("/process-tts/")
async def process_tts(input: TTSRequest):
    """
    Endpoint to process text-to-speech using OpenAI API.
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
        
        return {"message": "TTS processing completed", "file_path": file_path}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing TTS: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
