# examigo/services/pdf_processor.py

import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

# Constants for processing
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2" # For embeddings

def process_pdf(document):
    """
    Process a PDF document, splitting it into chunks and creating a vector store.
    Args:
        document: The Document model object containing the uploaded PDF
    Returns:
        str: Path to the saved vector store
    """
    pdf_path = document.file.path
    vector_dir = os.path.join('media', 'vector_stores')
    os.makedirs(vector_dir, exist_ok=True)
    vector_store_path = os.path.join(vector_dir, f"document_{document.id}")
    
    try:
        loader = PyPDFLoader(pdf_path)
        pdf_documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        chunks = text_splitter.split_documents(pdf_documents)
        processed_chunks = [
            Document(page_content=chunk.page_content, metadata=chunk.metadata)
            for chunk in chunks
        ]
        embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
        
        # Check if the vector store already exists
        if os.path.exists(vector_store_path + ".faiss"):
            # If it exists, load it
            vector_store = FAISS.load_local(vector_store_path, embeddings, allow_dangerous_deserialization=True)
        else:
            # If it doesn't exist, create a new one from the processed chunks
            vector_store = FAISS.from_documents(processed_chunks, embeddings)
            
        # Save the vector store
        vector_store.save_local(vector_store_path)
        return vector_store_path
    except Exception as e:
        print(f"Error processing PDF: {e}")
        raise e