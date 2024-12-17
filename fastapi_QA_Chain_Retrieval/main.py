from fastapi import FastAPI, File, UploadFile
from utils import load_split_pdf_file, load_split_docx_file, load_split_text_file, QA_Chain_Retrieval, QdrantInsertRetrievalAll, Conversational_Retrieval
import tempfile
import os
from langchain_openai import OpenAIEmbeddings
#import uvicorn
from zipfile import ZipFile
import shutil
from pydantic import BaseModel
from rag_db import SessionLocal, Collections, ChatHistory
import tempfile , random , datetime, string
from langchain_openai import ChatOpenAI
from langchain_core.prompts.chat import ChatPromptTemplate
from operator import itemgetter
import ast, uuid
from typing import List
from fastapi import Form
from fastapi.responses import JSONResponse
from fastapi import status

from dotenv import load_dotenv
load_dotenv()

qdrant_api_key = os.getenv("QDRANT_API_KEY")
qdrant_url = os.getenv("QDRANT_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

Embeddings_model = "text-embedding-3-small"


embeddings = OpenAIEmbeddings(model = Embeddings_model, api_key = OPENAI_API_KEY)

my_qdrant = QdrantInsertRetrievalAll(api_key = qdrant_api_key, url = qdrant_url)

app = FastAPI()

def process_file_by_extension(file_path: str, file_extension: str):
    """
    Process a file based on its extension and return the chunks.
    
    Args:
        file_path (str): Path to the file.
        file_extension (str): Extension of the file (e.g., 'docx', 'pdf', 'txt').
    
    Returns:
        list: Chunks extracted from the file.
    """
    if file_extension == "docx":
        return load_split_docx_file(file_path)
    elif file_extension == "pdf":
        return load_split_pdf_file(file_path)
    elif file_extension == "txt":
        return load_split_text_file(file_path)
    else:
        return [f"Unsupported file type: {file_extension}"]

@app.post("/upload_files/")
async def upload_files(files: List[UploadFile],chatbot_id:str = Form(...)):
    chatbot_id = chatbot_id
    session = SessionLocal()
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small",api_key=os.getenv("OPENAI_API_KEY"))
    try: 

        collection = session.query(Collections).filter_by(chatbot_id=chatbot_id).first()
        if collection:
            collection_name = collection.collection
        else:
            # Define a single collection name
            random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            current_time = datetime.datetime.now().strftime("%y%m%d_%H%M")
            collection_name = f"collection_{current_time}_{random_string}"
            collection_name = collection_name+"_"+str(chatbot_id)

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
            # Store in database
            if not collection:
                new_collection = Collections(collection=collection_name,chatbot_id=chatbot_id)
                session.add(new_collection)
                session.commit()

            insertion_status = "Insertion successful"
        except Exception as e:
            insertion_status = f"Insertion failed: {str(e)}"

        data = {
            "vecDbPath": insertion_status,
            "collection_name": collection_name
        }

        return data
        #return {"data": data, "file_results": results}
    finally:
        session.close()

# class QueryRequest(BaseModel):
#     query: str

# @app.post("/retrieve")
# async def retrieve(request: QueryRequest):
#     try:
#         # Extract the query from the request
#         query_user = request.query

#         # Perform retrieval from Qdrant
#         vectorstore = my_qdrant.retrieval(embeddings=embeddings, collection_name=collection_name)
#         results = QA_Chain_Retrieval(query=query_user, qdrant_vectordb=vectorstore)

#         # If results are found, return the content
#         return {"content": results.content}
#     except Exception as e:
#         # Return a user-friendly error message
#         return {"error": str(e)}


# Updated QueryRequest model
class QueryRequest(BaseModel):
    collection_name: str
    query: str

@app.post("/retrieve")
async def Retrieval(request: QueryRequest):
    collection_name_user = request.collection_name
    query_user = request.query
    print(type(query_user))

    session = SessionLocal()
    try:
        # Fetch collection details using UUID
        collection = session.query(Collections).filter_by(collection=collection_name_user).first()
        print(type(collection))
        if not collection:
            return JSONResponse(content={"message": "Collection name not found"}, status_code=status.HTTP_404_NOT_FOUND)

        # Fetch chat history using collection_uuid
        history_name = session.query(ChatHistory).filter_by(collection_name=collection_name_user).order_by(ChatHistory.id.desc()).limit(30).all()

        chat_history = []
        for chat in history_name:
            if chat.query:
                chat_history.append(f"User: {chat.query}")
            if chat.response:
                chat_history.append(f"AI response: {chat.response}")

        collection_ = collection.collection
        print(type(collection_))

        # Initialize embeddings and LLM model
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
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
            new_history = ChatHistory(
                collection_name=collection_,
                query=query_user,
                response=message
            )
            session.add(new_history)
            session.commit()
            return JSONResponse(content={"message": "Response Generated Successfully!", "data": message}, status_code=status.HTTP_200_OK)

        # Handle non-greeting queries
        vectorstore = my_qdrant.retrieval(embeddings=embeddings, collection_name=collection_)
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 10})
        results = Conversational_Retrieval(query = query_user, history = chat_history, retriever = retriever)

        new_history = ChatHistory(
            collection_name=collection_,
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
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)