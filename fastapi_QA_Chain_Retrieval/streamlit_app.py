import streamlit as st
import requests

# Define the base URL for your FastAPI service
FASTAPI_URL = "http://127.0.0.1:8000"  # Update with your deployed FastAPI endpoint if applicable

# Application Title
st.title("Document Upload and Query Application")

# File Upload Section
st.header("Upload Files")
uploaded_files = st.file_uploader(
    "Upload your documents (PDF, DOCX, TXT, ZIP):",
    type=["pdf", "docx", "txt", "zip"],
    accept_multiple_files=True
)

if st.button("Upload"):
    if uploaded_files:
        files = [("files", (file.name, file.read(), file.type)) for file in uploaded_files]
        response = requests.post(f"{FASTAPI_URL}/upload_files/", files=files)

        if response.status_code == 200:
            data = response.json()
            st.success(data.get("message", "File processing completed successfully."))
        else:
            st.error(f"Failed to upload files. Error: {response.text}")
    else:
        st.warning("Please upload at least one file.")

# Query Section
st.header("Retrieve Information")
query = st.text_input("Enter your query:")

if st.button("Retrieve"):
    if query:
        payload = {"query": query}  # Send the query as a JSON object
        headers = {"Content-Type": "application/json"}  # Ensure correct headers

        # Make the POST request to the FastAPI retrieve endpoint
        response = requests.post(f"{FASTAPI_URL}/retrieve", json=payload, headers=headers)

        if response.status_code == 200:
            result = response.json()

            # Check if content exists in the result
            if "content" in result:
                st.success("Query processed successfully!")
                st.write(result["content"])
            else:
                st.warning("No content found for the query.")
        else:
            # Display error from the FastAPI service
            st.error(f"Failed to process query. Error: {response.text}")
    else:
        st.warning("Please enter a query.")

