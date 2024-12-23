import streamlit as st
import requests

# Streamlit App Title
st.title("AI Image Generator")

# Input fields for user to specify image generation parameters
st.subheader("Enter Image Details")

prompt = st.text_area("Image Prompt", placeholder="Describe the image you want to generate...", max_chars=500)

size = st.selectbox(
    "Select Image Size", 
    ["1024x1024", "1024x1792", "1792x1024"], 
    index=0 # Default to 1024x1024
)

quality = st.selectbox(
    "Select Image Quality", 
    ["standard", "hd"], 
    index=0  # Default to standard
)

n = st.number_input(
    "Number of Images", 
    min_value=1, max_value=1, value=1, step=1  # Default to 1 for dalle3 
)

# Button to trigger image generation
if st.button("Generate Image"):
    if not prompt.strip():
        st.error("Please provide a prompt to generate images.")
    else:
        # Send POST request to the FastAPI server
        try:
            with st.spinner("Generating images..."):
                response = requests.post(
                    "http://127.0.0.1:8000/generate-image/",  # Update with your FastAPI endpoint if hosted elsewhere
                    json={"prompt": prompt, "size": size, "quality": quality, "n": n}
                )

                if response.status_code == 200:
                    image_urls = response.json().get("image_urls", [])

                    if image_urls:
                        st.success(f"Generated {len(image_urls)} image(s):")

                        # Display each image
                        for idx, url in enumerate(image_urls):
                            st.image(url, caption=f"Image {idx + 1}", use_column_width=True)
                    else:
                        st.warning("No images were generated. Please try again with a different prompt.")
                else:
                    st.error(f"Error {response.status_code}: {response.json().get('detail', 'Unknown error')}.")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
