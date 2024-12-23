from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from openai import OpenAI
import uvicorn

# Initialize the FastAPI app
app = FastAPI()

# OpenAI client initialization
client = OpenAI()

"""
https://platform.openai.com/docs/guides/images

The image generations endpoint allows you to create an original image given a text prompt. When using DALL·E 3, images can have a size of 1024x1024, 1024x1792 or 1792x1024 pixels.

By default, images are generated at standard quality, but when using DALL·E 3 you can set quality: "hd" for enhanced detail. Square, standard quality images are the fastest to generate.

You can request 1 image at a time with DALL·E 3 (request more by making parallel requests) or up to 10 images at a time using DALL·E 2 with the n parameter.
"""

# Define a Pydantic model for user input
class ImagePrompt(BaseModel):
    prompt: str
    size: Optional[str] = "1024x1024"  # Default size
    quality: Optional[str] = "standard"  # Default quality
    n: Optional[int] = 1  # Default number of images

@app.post("/generate-image/")
async def generate_image(input_data: ImagePrompt):
    """
    Endpoint to generate an image from a user-defined prompt using OpenAI API.
    """
    try:
        # Call the OpenAI API
        response = client.images.generate(
            model="dall-e-3",
            prompt=input_data.prompt,
            size=input_data.size,
            quality=input_data.quality,
            n=input_data.n,
        )
        
        # Return the URL(s) of generated images
        return {"image_urls": [img.url for img in response.data]}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run the server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
