from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List
import base64
import requests
from openai import OpenAI

app = FastAPI()

client = OpenAI()

# Function to encode an image to base64
def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

# Function to encode an image from a URL to base64
def encode_image_from_url(image_url):
    response = requests.get(image_url)
    if response.status_code == 200:
        return base64.b64encode(response.content).decode('utf-8')
    else:
        raise HTTPException(status_code=400, detail=f"Failed to fetch the image from URL: {image_url}")

# Function to send the image to OpenAI API and get a response
def get_openai_response(base64_image):
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

# Pydantic model for input validation
class UrlList(BaseModel):
    urls: List[str]

@app.post("/process-imgs/urls")
async def process_images_from_urls(url_list: UrlList):
    responses = []
    for url in url_list.urls:
        try:
            base64_image = encode_image_from_url(url)
            response = get_openai_response(base64_image)
            responses.append({"url": url, "response": response})
        except Exception as e:
            responses.append({"url": url, "error": str(e)})
    return responses

@app.post("/process-imgs/upload")

async def process_uploaded_image(file: UploadFile = File(...)):
    try:
        base64_image = encode_image(file.file)
        response = get_openai_response(base64_image)
        return {"filename": file.filename, "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)