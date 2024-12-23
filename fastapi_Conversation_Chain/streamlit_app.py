import streamlit as st
import requests

# Set FastAPI endpoint
FASTAPI_ENDPOINT = "http://localhost:8000/Conversation_chain"

# Streamlit UI
def main():
    st.title("Conversational Chain Application")
    st.subheader("Interact with the Chatbot")

    # Input fields
    chatbot_id = st.text_input("Chatbot ID", placeholder="Enter a unique chatbot ID")
    user_query = st.text_area("Your Query", placeholder="Type your message here...")

    # Submit button
    if st.button("Send Query"):
        if not chatbot_id or not user_query:
            st.warning("Please fill in both the Chatbot ID and your query.")
        else:
            with st.spinner("Processing your query..."):
                try:
                    # Send request to FastAPI
                    response = requests.post(FASTAPI_ENDPOINT, json={"chatbot_id": chatbot_id, "query": user_query})

                    if response.status_code == 200:
                        data = response.json()
                        st.success("Response Generated Successfully!")
                        st.write("### AI Response:")
                        st.write(data.get("data", "No response data available."))
                    else:
                        st.error(f"Error: {response.status_code}")
                        st.write(response.json())

                except requests.exceptions.RequestException as e:
                    st.error("Failed to connect to the server. Please ensure the FastAPI service is running.")
                    st.write(str(e))

if __name__ == "__main__":
    main()
