import streamlit as st

from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from dotenv import load_dotenv
import os

load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')


# Define a simple prompt template
template = """
You are a helpful assistant. Answer the question: {question}
"""

prompt = PromptTemplate(
    input_variables=["question"],
    template=template,
)

# Set up the OpenAI model with LangChain
llm = OpenAI(
    openai_api_key=openai_api_key,
    temperature=0.7,  # Adjust as per your requirement
)

# Create a LangChain pipeline
chain = LLMChain(
    llm=llm,
    prompt=prompt,
)

def ask_question(chain, question: str) -> str:
    try:
        response = chain.run(question=question)
        return response
    except Exception as e:
        print(f"Error: {e}")
        return "Something went wrong. Please try again."



st.title("LangChain + OpenAI Chatbot")

question = st.text_input("Ask me anything:")

if st.button("Get Answer"):
    response = ask_question(chain, question)
    st.write(response)

