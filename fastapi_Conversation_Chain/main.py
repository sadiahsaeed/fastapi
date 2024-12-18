from fastapi import FastAPI, File, UploadFile
from utils import QdrantInsertRetrievalAll, Conversational_Chain
import tempfile
import os
from langchain_openai import OpenAIEmbeddings
import uvicorn
from pydantic import BaseModel
from conv_ret_db import SessionLocal, ConversationChatHistory
import tempfile , random , datetime, string
from langchain_openai import ChatOpenAI
from langchain_core.prompts.chat import ChatPromptTemplate
from operator import itemgetter
import ast
from fastapi.responses import JSONResponse
from fastapi import status

from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

Embeddings_model = "text-embedding-3-small"

embeddings = OpenAIEmbeddings(model = Embeddings_model, api_key = OPENAI_API_KEY)

app = FastAPI()

# Updated QueryRequest model
class QueryRequest(BaseModel):
    chatbot_id: str
    query: str

@app.post("/Conversation_chain")
async def Convo_chain(request: QueryRequest):
    chatbot_id_user = request.chatbot_id
    query_user = request.query
    print("query_user: ", type(query_user))
    print("Received chatbot_id_user:", chatbot_id_user)

    session = SessionLocal()
    try:
        # Query the database to find an existing chatbot_id
        chatbot_id_table = session.query(ConversationChatHistory).filter_by(chatbot_id=chatbot_id_user).first()
        print(chatbot_id_table)
        
        if chatbot_id_table:
            # Use the existing chatbot_id if found
            chatbot_id = chatbot_id_table.chatbot_id
            print(f"Existing chatbot_id found: {chatbot_id}")
        else:
            # Generate a new chatbot_id if no record is found
            chatbot_id = chatbot_id_user
            print(f"Generated new chatbot_id: {chatbot_id}")
        
        conversation_history = session.query(ConversationChatHistory).filter_by(chatbot_id=chatbot_id).order_by(ConversationChatHistory.id.desc()).limit(30).all()

        chat_history = []
        for chat in conversation_history:
            if chat.query:
                chat_history.append(f"User: {chat.query}")
            if chat.response:
                chat_history.append(f"AI response: {chat.response}")

        # Initialize embeddings and LLM model
        #embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        llm_model = ChatOpenAI(model='gpt-4o-mini', openai_api_key=os.getenv("OPENAI_API_KEY"), temperature=0)

        # Greeting check functionality
        greeting_prompt = """
            You are an expert in classifying whether the provided user query is related to a greeting or not. 
            If it is a greeting, classify it as 'yes' and generate a greeting response. 
            Otherwise, classify it as 'no' and return 'statusCode:404' in greeting_response. 
            provided user query: {query}
            
            The output should be in the format: ["yes/no", "greeting_response"]
            """
        greeting_prompt = ChatPromptTemplate.from_template(greeting_prompt)

        query_input = {"query": query_user}

        # Check for greeting
        greeting_chain = ({"query": itemgetter("query")}  | greeting_prompt | llm_model)
        greeting_response = greeting_chain.invoke(query_input)
        response = ast.literal_eval(greeting_response.content)
        label = response[0]

        if label.lower().endswith("yes"):
            message = response[1]
            new_history = ConversationChatHistory(
                chatbot_id=chatbot_id,
                query=query_user,
                response=message
            )
            session.add(new_history)
            session.commit()
            return JSONResponse(content={"message": "Response Generated Successfully!", "data": message}, status_code=status.HTTP_200_OK)

        # Handle non-greeting queries
        results = Conversational_Chain(query = query_user, history = chat_history)

        new_history = ConversationChatHistory(
            chatbot_id=chatbot_id,
            query=query_user,
            response=results
        )
        session.add(new_history)
        session.commit()

        #return {"message": "Response Generated Successfully", "data": results}
        return JSONResponse(content={"message": "Response Generated Successfully!", "data": results}, status_code=status.HTTP_200_OK)


    finally:
        session.close()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)