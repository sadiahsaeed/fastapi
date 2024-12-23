import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = "http://127.0.0.1:8000"  # Update with your FastAPI host and port

st.title("Document Upload and Retrieval System")

st.sidebar.header("Navigation")
navigation = st.sidebar.radio("Select a page:", ["Upload Files", "Retrieve Query"])

# File Upload Page
if navigation == "Upload Files":
    st.header("Upload Files")
    chatbot_id = st.text_input("Enter Chatbot ID", value="")
    
    uploaded_files = st.file_uploader("Upload your files (Supports .docx, .pdf, .txt, .zip):", 
                                      accept_multiple_files=True)

    if st.button("Upload"):
        if not chatbot_id or not uploaded_files:
            st.error("Please provide both a Chatbot ID and files to upload.")
        else:
            files = [
                ("files", (file.name, file, file.type)) for file in uploaded_files
            ]
            data = {"chatbot_id": chatbot_id}
            
            with st.spinner("Uploading files..."):
                try:
                    response = requests.post(f"{API_BASE_URL}/upload_files/", 
                                            files=files, 
                                            data=data)
                    if response.status_code == 200:
                        result = response.json()
                        st.success("Files uploaded successfully!")
                        
                        # Displaying parsed results in a user-friendly format
                        vec_db_path = result.get("vecDbPath", "No info provided")
                        collection_name = result.get("collection_name", "No info provided")
                        
                        st.write(f"**Vector Database Path:** {vec_db_path}")
                        st.write(f"**Collection Name:** {collection_name}")
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

# Retrieve Query Page
elif navigation == "Retrieve Query":
    st.header("Retrieve Query")

    collection_name = st.text_input("Enter Collection Name", value="")
    user_query = st.text_area("Enter your query", value="")

    if st.button("Retrieve"):
        if not collection_name or not user_query:
            st.error("Please provide both a Collection Name and a query.")
        else:
            payload = {
                "collection_name": collection_name,
                "query": user_query
            }
            
            with st.spinner("Retrieving response..."):
                try:
                    response = requests.post(f"{API_BASE_URL}/retrieve", json=payload)
                    if response.status_code == 200:
                        result = response.json()
                        st.success("Response retrieved successfully!")
                        st.write(result.get("data", ""))
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

