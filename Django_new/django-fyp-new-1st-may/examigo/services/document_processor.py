import os
import logging
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

def process_document_for_chat(document_path, document_id):
    """
    Processes a document by reading its text, splitting into chunks,
    creating embeddings, and saving to a FAISS vector store.
    """
    # Try reading as plain text
    try:
        with open(document_path, 'r', encoding='utf-8') as file:
            text = file.read()
    except Exception:
        # Fallback for PDF files
        loader = PyPDFLoader(document_path)
        pages = loader.load()
        text = "\n".join([page.page_content for page in pages])

    # Split text into manageable chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_text(text)

    # Generate embeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # Create a FAISS vector store
    vectorstore = FAISS.from_texts(chunks, embeddings)

    # Ensure directory exists and save the vector store
    os.makedirs('media/vector_stores', exist_ok=True)
    vectorstore.save_local(f"media/vector_stores/document_{document_id}")

    return len(chunks)


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
