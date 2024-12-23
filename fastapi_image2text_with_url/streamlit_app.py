import streamlit as st
import requests
import base64
from pydantic import BaseModel
from typing import List

# -----------------------------------------------------------
# 1. Replace with your actual OpenAI usage
# -----------------------------------------------------------
# If you are using the official `openai` library, you might do:
#     import openai
#     openai.api_key = "YOUR_API_KEY"
# If you have a custom client like `OpenAI()`, then import it similarly.
#
# In this example, we'll mimic your usage from the question:
from openai import OpenAI

# Initialize the client
client = OpenAI()


# -----------------------------------------------------------
# 2. Define helper functions (same as in your FastAPI code)
# -----------------------------------------------------------

def encode_image(image_file):
    """
    Encode an uploaded image file as a Base64 string.
    """
    return base64.b64encode(image_file.read()).decode('utf-8')

def encode_image_from_url(image_url):
    """
    Fetch an image from URL and encode as a Base64 string.
    Raises HTTPException if the image cannot be retrieved.
    """
    response = requests.get(image_url)
    if response.status_code == 200:
        return base64.b64encode(response.content).decode('utf-8')
    else:
        # Instead of HTTPException, raise a standard Python exception here
        raise Exception(f"Failed to fetch the image from URL: {image_url}")

def get_openai_response(base64_image):
    """
    Send the Base64-encoded image to the OpenAI API
    and return the text response.
    """
    # Example usage based on your code snippet:
    # Adjust according to your actual openai/ client usage.
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Adjust to the actual model name or ID you use
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What is in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    },
                ],
            }
        ],
    )
    return response.choices[0].message.content


# -----------------------------------------------------------
# 3. Define the Streamlit app layout and logic
# -----------------------------------------------------------
def main():
    st.title("Image Processing with GPT-4-like Model")

    st.write(
        "This Streamlit app replicates the functionality of the FastAPI example "
        "you provided. You can either process images from URLs or upload an image "
        "directly and send it to OpenAI to get a response describing what's in the image."
    )

    # -- Tabs or sections in Streamlit
    tab1, tab2 = st.tabs(["Process Images from URLs", "Process Uploaded Image"])

    with tab1:
        st.subheader("Process Images from URLs")
        st.write("Enter one or more image URLs (one per line):")
        urls_text = st.text_area("Image URLs", height=150, placeholder="https://example.com/image1.jpg\nhttps://example.com/image2.png")
        if st.button("Process URLs"):
            # Split the text area by lines to get a list of URLs
            urls = [url.strip() for url in urls_text.split("\n") if url.strip()]
            if not urls:
                st.warning("Please provide at least one valid URL.")
            else:
                responses = []
                for url in urls:
                    try:
                        base64_image = encode_image_from_url(url)
                        response = get_openai_response(base64_image)
                        responses.append({"url": url, "response": response})
                    except Exception as e:
                        responses.append({"url": url, "error": str(e)})

                # Display results
                for resp in responses:
                    st.write("---")
                    st.write(f"**URL**: {resp['url']}")
                    if "error" in resp:
                        st.error(f"Error: {resp['error']}")
                    else:
                        st.write(f"**Response**: {resp['response']}")

    with tab2:
        st.subheader("Process Uploaded Image")
        uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff", "ico"])
        if uploaded_file is not None:
            # Validate content type (as in your FastAPI code)
            if uploaded_file.type not in ["image/png", "image/jpeg", "image/gif", "image/webp", "image/bmp", "image/tiff", "image/x-icon"]:
                st.error("Invalid file type. Only PNG, JPG, GIF, WEBP, BMP, TIFF, ICO are allowed.")
            else:
                if st.button("Process Uploaded Image"):
                    try:
                        # Encode and send to OpenAI
                        base64_image = encode_image(uploaded_file)
                        response = get_openai_response(base64_image)
                        st.write(f"**Filename:** {uploaded_file.name}")
                        st.write(f"**Response:** {response}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
