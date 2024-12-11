from fastapi import FastAPI, File, UploadFile
from utils import load_split_pdf_file, load_split_docx_file, load_split_text_file, QA_Chain_Retrieval, QdrantInsertRetrievalAll
import tempfile
import os
from langchain_openai import OpenAIEmbeddings
#import uvicorn

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
async def upload_file(files: list[UploadFile] = File(...)):
    results = []
    all_chunks = [] 

    for file in files:
        try:

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
                chunks = f"Unsupported file type: {file_extension}"
            
            # Append results for each file
            results.append({"filename": file.filename, "content": chunks[:500]})  # Truncate content

            # Collect chunks
            all_chunks.extend(chunks)

        except Exception as e:
            results.append({"filename": file.filename, "error": str(e)})

        finally:
            os.unlink(tmp_file_path)  # Remove the temporary file

    # After processing all files, insert all chunks into qdrant
    try:
        my_qdrant.insertion(all_chunks, embeddings, collection_name)
        insertion_status = "Insertion successful"
    except Exception as e:
        insertion_status = f"Insertion failed: {str(e)}"

    # Return the combined result
    data = {
        "vecDbPath": insertion_status,
        "collection_name": collection_name  # Include collection name in the response
    }

    return {"data": data, "file_results": results}


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