from fastapi import FastAPI, UploadFile, File
from typing import Optional
import base64
from openai import OpenAI
from fastapi.responses import JSONResponse
client = OpenAI()
app = FastAPI()

@app.post("/process-image/")
async def process_image(file: Optional[UploadFile] = File(None)):
    try:
        # if file.content_type not in ["image/png", "image/jpeg"]:
        #     return JSONResponse(content={"error": "Invalid file type. Only PNG and JPG are allowed."}, status_code=400)
        base64_image = encode_image(file.file)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What is in this image?"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ],
        )
        return response.choices[0].message.content

     
    except Exception as e:
            return JSONResponse(status_code=500, content={"error": f"Failed to process uploaded file: {str(e)}"})

def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)