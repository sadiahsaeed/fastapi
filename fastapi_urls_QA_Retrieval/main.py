from fastapi import FastAPI, File, UploadFile
from utils import process_file_by_extension,  QA_Chain_Retrieval, QdrantInsertRetrievalAll
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tempfile
import os
from langchain_openai import OpenAIEmbeddings
#import uvicorn
from zipfile import ZipFile
import shutil

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from langchain.document_loaders import WebBaseLoader

from dotenv import load_dotenv
load_dotenv()

embeddings = OpenAIEmbeddings()

qdrant_api_key = os.getenv("QDRANT_API_KEY")
qdrant_url = os.getenv("QDRANT_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
collection_name = "testing_url"

my_qdrant = QdrantInsertRetrievalAll(api_key = qdrant_api_key, url = qdrant_url)

app = FastAPI()

# Define a Pydantic model for input validation
class UrlList(BaseModel):
    urls: List[str]

@app.post("/process-urls/")
async def process_urls(url_list: UrlList):
    """
    Endpoint to process a list of URLs using WebBaseLoader.
    """
    try:
        chunk_size = 500
        chunk_overlap = 50
        # Initialize the WebBaseLoader with the provided URLs
        all_chunks = []
        documents = []
        for url in url_list.urls:
            loader = WebBaseLoader(url)
            # Load and extend documents
            documents.extend(loader.load())
        
        # Extract content from the documents
        #results = [{"url": doc.metadata.get("source"), "content": doc.page_content} for doc in documents]

        urls_content = [doc.page_content for doc in documents]
        textsplit = RecursiveCharacterTextSplitter(
            chunk_size = chunk_size, chunk_overlap = chunk_overlap, length_function=len)

        url_chunks = textsplit.create_documents(urls_content)
        all_chunks.extend(url_chunks)
        #return {"success": True, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        my_qdrant.insertion(all_chunks, embeddings, collection_name)
        insertion_status = "Insertion successful"
    except Exception as e:
        insertion_status = f"Insertion failed: {str(e)}"

    data = {
        "vecDbPath": insertion_status,
        "collection_name": collection_name
    }
    return data

#now do this with history
        
    
@app.post("/upload_files/")
async def upload_files(files: list[UploadFile] = File(...)):
    results = []
    all_chunks = []  # To accumulate chunks from all files

    for file in files:
        try:
            contents = await file.read()
            file_extension = file.filename.split(".")[-1].lower()

            if file_extension == "zip":
                fd, tmp_file_path = tempfile.mkstemp(suffix=".zip")
                with os.fdopen(fd, 'wb') as tmp_file:
                    tmp_file.write(contents)

                extract_dir = tempfile.mkdtemp()
                try:
                    with ZipFile(tmp_file_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)

                    for extracted_file in os.listdir(extract_dir):
                        extracted_file_path = os.path.join(extract_dir, extracted_file)
                        extracted_file_extension = extracted_file.split(".")[-1].lower()

                        with open(extracted_file_path, 'rb') as ef:
                            extracted_contents = ef.read()

                        chunks = process_file_by_extension(extracted_file_path, extracted_file_extension)

                        results.append({"filename": extracted_file, "content_preview": chunks[:500]})
                        all_chunks.extend(chunks)
                finally:
                    shutil.rmtree(extract_dir)
                    os.unlink(tmp_file_path)

            else:
                fd, tmp_file_path = tempfile.mkstemp(suffix=f".{file_extension}")
                with os.fdopen(fd, 'wb') as tmp_file:
                    tmp_file.write(contents)

                chunks = process_file_by_extension(tmp_file_path, file_extension)

                results.append({"filename": file.filename, "content_preview": chunks[:500]})
                all_chunks.extend(chunks)

                os.unlink(tmp_file_path)

        except Exception as e:
            results.append({"filename": file.filename, "error": str(e)})

    try:
        my_qdrant.insertion(all_chunks, embeddings, collection_name)
        insertion_status = "Insertion successful"
    except Exception as e:
        insertion_status = f"Insertion failed: {str(e)}"

    data = {
        "vecDbPath": insertion_status,
        "collection_name": collection_name
    }

    return data
    #return {"data": data, "file_results": results}


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