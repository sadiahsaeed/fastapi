from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.schema import BaseOutputParser


def QA_Chain(query: str) -> str:
    try:
        # Define the prompt template
        prompt_str = """
        Answer the user question clearly and concisely:
        Question: {question}
        Answer:
        """
        prompt = ChatPromptTemplate.from_template(prompt_str)
        
        # Initialize the chat model
        chat_llm = ChatOpenAI(model_name="gpt-4", temperature=0)
        
        # Build the LLM chain
        chain = LLMChain(llm=chat_llm, prompt=prompt)
        
        # Run the chain with the user's query
        response = chain.run({"question": query})
        
        return response
    
    except Exception as e:
        return f"Error executing QA_Chain: {str(e)}"
