from langchain_core.output_parsers import StrOutputParser

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from operator import itemgetter

def QA_Chain(query):
    try:
        # Prompt template string
        prompt_str = """
        Answer the user question:
        Question: {question}
        """
        
        # Create a chat prompt template
        _prompt = ChatPromptTemplate.from_template(prompt_str)
        
        # Set up the chain components
        chat_llm = ChatOpenAI(model_name="gpt-4o-mini")

        
        query_fetcher = itemgetter("question")
        setup = {
            "question": query_fetcher
        }

        output_parser = StrOutputParser()

        # Define the final chain
        _chain = setup | _prompt | chat_llm | output_parser
        
        # Execute the chain and fetch the response
        response = _chain.invoke({"question": query})
        return response
    
    except Exception as e:
        return f"Error executing retrieval chain: {str(e)}"
