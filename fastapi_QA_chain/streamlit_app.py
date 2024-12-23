import streamlit as st
import os
from dotenv import load_dotenv

# Import your QA_Chain and embeddings just like you would in FastAPI
from utils import QA_Chain
from langchain_openai import OpenAIEmbeddings

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize embeddings (if needed for your QA_Chain)
embeddings = OpenAIEmbeddings()

def main():
    st.title("QA Application using Streamlit")

    st.write("Enter your query below and click **Submit** to get the response from the QA chain.")

    # Text input for the query
    query_user = st.text_input("Your Query", "")

    # Submit button
    if st.button("Submit"):
        if not query_user.strip():
            st.warning("Please enter a valid query.")
        else:
            try:
                # Call your QA_Chain function
                result = QA_Chain(query=query_user)
                st.success("Response from QA_Chain:")
                st.write(result)
            except Exception as e:
                st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
