from fastapi import FastAPI, File, UploadFile
from utils import load_split_pdf_file, load_split_docx_file, load_split_text_file, QA_Chain_Retrieval, QdrantInsertRetrievalAll
import tempfile
import os
from langchain_openai import OpenAIEmbeddings
import uvicorn

from dotenv import load_dotenv
load_dotenv()

embeddings = OpenAIEmbeddings()

qdrant_api_key = os.getenv("QDRANT_API_KEY")
qdrant_url = os.getenv("QDRANT_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
collection_name = "testing"

my_qdrant = QdrantInsertRetrievalAll(api_key = qdrant_api_key, url = qdrant_url)

app = FastAPI()

@app.post("/upload_file/")
async def upload_file(file: UploadFile = File(...)):

    contents = await file.read()

    file_extension = file.filename.split(".")[-1].lower()

    # Create a temporary file using mkstemp
    fd, tmp_file_path = tempfile.mkstemp(suffix=f".{file_extension}")

    with os.fdopen(fd, 'wb') as tmp_file:
        tmp_file.write(contents)

    if file_extension == "docx":
        chunks = load_split_docx_file(tmp_file_path)
    elif file_extension == "pdf":
        chunks = load_split_pdf_file(tmp_file_path)
    elif file_extension == "txt":
        chunks = load_split_text_file(tmp_file_path)
    else:
        TypeError("not supported file format")


    # insert into qdrant
    my_qdrant.insertion(chunks,embeddings,collection_name)   
    insertion = "insertion successfull"

    data = {
        "vecDbPath": insertion , 
        "collection_name": collection_name # to return collection name as well
    }
    os.unlink(tmp_file_path)
    return data, chunks


@app.post("/retrieve")
async def retrieve(query: str):
    query_user = query
    # Retrieve results from Qdrant based on the query
    vectorstore = my_qdrant.retrieval(embeddings=embeddings,collection_name=collection_name)
    
    prompt_template = """You are assistant. Use the following pieces of {CONTEXT} to generate an answer to the provided question. keep in mind that if you are not able to find any relevant answer in the document then return message like "Query's Answer not found in the provided document"
    question: {question}.
    Helpful Answer:"""
    results = QA_Chain_Retrieval(query=query_user,qdrant_vectordb=vectorstore)
    print(results)
    return results.content

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)