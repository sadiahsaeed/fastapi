from fastapi import FastAPI
from utils import QA_Chain
import os
from langchain_openai import OpenAIEmbeddings
import uvicorn

from dotenv import load_dotenv
load_dotenv()

embeddings = OpenAIEmbeddings()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()

@app.post("/get_query/")
async def query(query:str):
    query_user = query
    try:
        results = QA_Chain(query=query_user)

        # If results are found, return the content
        return {"result": results}
    except Exception as e:
        # Return a user-friendly error message
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)