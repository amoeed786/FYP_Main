# examigo/services/pdf_processor.py

import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
import logging

from langchain_google_genai import ChatGoogleGenerativeAI
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
    
logger = logging.getLogger(__name__)

def generate_ai_response(document_id, query):
    try:
        # Define path to vector store
        vector_path = os.path.join("media", "vector_stores", f"document_{document_id}")
        index_file = os.path.join(vector_path, "index.faiss")
        pickle_file = os.path.join(vector_path, "index.pkl")

        # Ensure the vector store files exist
        if not (os.path.exists(index_file) and os.path.exists(pickle_file)):
            print(document_id)
            logger.warning(f"Missing FAISS vector store for document {document_id}")
            return "Vector store not found. Please re-upload or re-process the document."

        # Load embeddings and vectorstore
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vectorstore = FAISS.load_local(vector_path, embeddings, allow_dangerous_deserialization=True)

        # Create a retriever
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

        # Gemini LLM initialization
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-preview-04-17", google_api_key=os.getenv("GOOGLE_API_KEY"))

        # Create the QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )

        # Ask the question and get a response
        result = qa_chain({"query": query})
        return result["result"]

    except Exception as e:
        logger.error(f"[generate_ai_response] Error for document {document_id}: {str(e)}")
        return f"Error generating response: {str(e)}"
