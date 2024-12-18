from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from langchain_openai import OpenAIEmbeddings 
import os

from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore , Qdrant
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient, models

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from operator import itemgetter
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.runnables import  RunnablePassthrough, RunnableParallel
from langchain.retrievers.document_compressors import LLMChainFilter
from langchain.retrievers import ContextualCompressionRetriever

from langchain.document_loaders import TextLoader


class QdrantInsertRetrievalAll:
    def __init__(self,api_key,url):
        self.url = url 
        self.api_key = api_key

    # Method to insert documents into Qdrant vector store
    def insertion(self,text,embeddings,collection_name):
        qdrant = QdrantVectorStore.from_documents(
        text,
        embeddings,
        url=self.url,
        prefer_grpc=True,
        api_key=self.api_key,
        collection_name=collection_name,
        force_recreate=True
        )
        print("insertion successfull")
        return qdrant

    # Method to retrieve documents from Qdrant vector store
    def retrieval(self,collection_name,embeddings):
        qdrant_client = QdrantClient(
        url=self.url,
        api_key=self.api_key,
        )
        qdrant_store = Qdrant(qdrant_client,collection_name=collection_name ,embeddings=embeddings)
        return qdrant_store
    

def Conversational_Chain(query, history):
        try:
            template = """you are expert chatbot assistant. you also have user history. Answer questions based on user history.
            history: {HISTORY}
            query:{QUESTION}
            """
            prompt = ChatPromptTemplate.from_template(template)
            model = ChatOpenAI(
                model="gpt-4o-mini", 
                openai_api_key=os.getenv("OPENAI_API_KEY"), 
                temperature=0
                )

            setup = RunnableParallel(
            {"HISTORY": RunnablePassthrough(), "QUESTION": RunnablePassthrough()}
            )

            output_parser = StrOutputParser()

            rag_chain = (
                setup
                | prompt
                | model
                | output_parser
            )
            input_dict = {"QUESTION": query, "HISTORY": history}
            response = rag_chain.invoke(str(input_dict))
            return response
        
        except Exception as e:
            return f"Error executing conversational retrieval chain: {str(e)}"