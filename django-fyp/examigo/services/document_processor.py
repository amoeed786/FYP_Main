# Create a new file: document_processor.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
import os

def process_document_for_chat(document_path, document_id):
    # Load document text
    with open(document_path, 'r', encoding='utf-8') as file:
        text = file.read()
    
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_text(text)
    
    # Create embeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Create vector store
    vectorstore = FAISS.from_texts(chunks, embeddings)
    
    # Save vector store
    os.makedirs('vector_stores', exist_ok=True)
    vectorstore.save_local(f"vector_stores/document_{document_id}")
    
    return len(chunks)

# In document_processor.py
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
import os

def generate_ai_response(document_id, query):
    # Load the vector store
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.load_local(f"vector_stores/document_{document_id}", embeddings)
    
    # Create retriever
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    # Create QA chain
    llm = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    
    # Generate response
    result = qa_chain({"query": query})
    
    return result["result"]