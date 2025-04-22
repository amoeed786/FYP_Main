# Standard library imports
import re
import os
from dotenv import load_dotenv  # Add this import at the top

# Load environment variables

# Third-party imports
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.schema import ChatMessage

# Constants
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
MODEL_NAME = "all-MiniLM-L6-v2"
OPENAI_MODEL = "gpt-3.5-turbo"
TEMPERATURE = 0.7

load_dotenv()
# Replace the hardcoded API_KEY with
API_KEY = os.getenv('OPENAI_API_KEY')
# PDF Processing Functions
def load_pdf(pdf_path):
    """
    Load and parse a PDF file into documents.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        list: List of document objects containing PDF content
    """
    loader = PyPDFLoader(pdf_path)
    return loader.load()

def split_documents(documents, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """
    Split documents into smaller chunks for better processing.
    
    Args:
        documents (list): List of documents to split
        chunk_size (int): Size of each chunk
        chunk_overlap (int): Overlap between chunks
        
    Returns:
        list: List of Document objects containing chunked content
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_documents(documents)
    return [Document(page_content=chunk.page_content, metadata=chunk.metadata) for chunk in chunks]

# Vector Store Functions
def create_vector_store(chunks):
    """
    Create a FAISS vector store from document chunks.
    
    Args:
        chunks (list): List of document chunks
        
    Returns:
        FAISS: Vector store containing document embeddings
    """
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    return FAISS.from_documents(chunks, embeddings)

def retrieve_chunks(vector_store, query, k=3):
    """
    Retrieve relevant document chunks based on a query.
    
    Args:
        vector_store (FAISS): Vector store containing document embeddings
        query (str): Search query
        k (int): Number of chunks to retrieve
        
    Returns:
        list: List of relevant document chunks
    """
    return vector_store.similarity_search(query, k=k)

# MCQ Generation Functions
def generate_mcqs(llm, relevant_chunks, topic, num_mcqs):
    """
    Generate MCQs using the language model.
    
    Args:
        llm: Language model instance
        relevant_chunks (list): List of relevant document chunks
        topic (str): Topic for MCQ generation
        num_mcqs (int): Number of MCQs to generate
        
    Returns:
        str: Generated MCQs in JSON-like format
    """
    # Combine context from chunks
    context = " ".join([
        chunk.page_content if hasattr(chunk, "page_content") else chunk.get("content", "")
        for chunk in relevant_chunks
    ])
    
    # Create system message with formatting instructions
    system_message = ChatMessage(role="system", content="""You are an expert educator specializing in creating MCQs.
    For each MCQ, provide:
    1. A clear question
    2. Four options labeled A) through D)
    3. The correct answer
    
    Format each MCQ as a JSON-like structure:
    {
        "question": "What is X?",
        "options": [
            "A) Option 1",
            "B) Option 2",
            "C) Option 3",
            "D) Option 4"
        ],
        "correct": "A"
    }
    
    Provide multiple MCQs separated by ###""")
    
    # Create user message with generation instructions
    user_message = ChatMessage(role="user", content=f"""
    Based on the following context, generate {num_mcqs} multiple-choice questions (MCQs) on the topic '{topic}':
    Context: {context}
    
    Generate exactly {num_mcqs} MCQs in the specified JSON-like format, separated by ###.
    Make sure each MCQ has exactly 4 options labeled A) through D).
    Create diverse questions that test different aspects of the topic.
    """)
    
    # Get response from language model
    response = llm([system_message, user_message])
    return response.content

def parse_mcqs(mcqs_text):
    """
    Parse generated MCQs text into structured format.
    
    Args:
        mcqs_text (str): Raw MCQs text in JSON-like format
        
    Returns:
        list: List of dictionaries containing parsed MCQs
    """
    mcqs_list = []
    raw_mcqs = mcqs_text.strip().split('###')
    
    for raw_mcq in raw_mcqs:
        try:
            # Extract question, options, and correct answer using regex
            question_match = re.search(r'"question":\s*"([^"]+)"', raw_mcq)
            options_match = re.findall(r'"options":\s*\[((?:[^]]+))\]', raw_mcq)
            correct_match = re.search(r'"correct":\s*"([^"]+)"', raw_mcq)
            
            if question_match and options_match and correct_match:
                question = question_match.group(1)
                options = [opt.strip().strip('"') for opt in options_match[0].split(',')]
                options = [opt.strip() for opt in options if opt.strip()]
                correct = correct_match.group(1)
                
                mcqs_list.append({
                    'question': question,
                    'options': options,
                    'correct': correct
                })
        except Exception as e:
            st.error(f"Error parsing MCQ: {e}")
            continue
            
    return mcqs_list

def process_pdf_for_mcqs(pdf_path, query, topic, num_mcqs):
    """
    Main function to process PDF and generate MCQs.
    
    Args:
        pdf_path (str): Path to PDF file
        query (str): Search query for relevant content
        topic (str): Topic for MCQ generation
        num_mcqs (int): Number of MCQs to generate
        
    Returns:
        list: List of generated MCQs
    """
    documents = load_pdf(pdf_path)
    chunks = split_documents(documents)
    vector_store = create_vector_store(chunks)
    k = max(3, num_mcqs)
    relevant_chunks = retrieve_chunks(vector_store, query, k=k)
    mcqs_text = generate_mcqs(llm, relevant_chunks, topic, num_mcqs)
    return parse_mcqs(mcqs_text)

# Initialize Language Model
llm = ChatOpenAI(
    model=OPENAI_MODEL,
    temperature=TEMPERATURE,
    openai_api_key=API_KEY
)

# Streamlit UI
def main():
    """Main function for Streamlit UI setup and interaction"""
    # Page configuration
    st.set_page_config(page_title="MCQ Generator", layout="wide")
    st.title("📚 AI-Powered MCQ Generator")
    st.markdown(
        """
        Create customized MCQs from your PDF notes with ease!  
        Select a topic, number of MCQs, and let AI generate the questions for you.
        """
    )
    
    # Sidebar inputs
    st.sidebar.header("Upload PDF")
    uploaded_file = st.sidebar.file_uploader("Upload your PDF file", type="pdf")
    
    st.sidebar.header("Customization Options")
    query = st.sidebar.text_input("Enter a Query", "Characteristics of computers")
    topic = st.sidebar.text_input("Enter a Topic", "Variable")
    num_mcqs = st.sidebar.slider("Number of MCQs", min_value=1, max_value=10, value=3)
    
    generate_button = st.sidebar.button("Generate MCQs")
    
    # MCQ generation and display
    if uploaded_file and generate_button:
        with st.spinner(f"Generating {num_mcqs} MCQs... Please wait."):
            try:
                # Save uploaded file
                pdf_path = f"./{uploaded_file.name}"
                with open(pdf_path, "wb") as f:
                    f.write(uploaded_file.read())
                
                # Generate MCQs
                mcqs = process_pdf_for_mcqs(pdf_path, query, topic, num_mcqs)
                
                # Display results
                st.subheader(f"Generated {len(mcqs)} MCQs for Topic: *{topic}*")
                
                for i, mcq in enumerate(mcqs, 1):
                    st.markdown(f"**Question {i}:** {mcq['question']}")
                    for option in mcq['options']:
                        st.markdown(f"{option}")
                    st.markdown(f"**Correct Answer:** {mcq['correct']}")
                    st.markdown("---")
                
                # Warning for fewer questions
                if len(mcqs) < num_mcqs:
                    st.warning(f"Note: Only {len(mcqs)} questions could be generated based on the available content. Try adjusting your query or topic for more questions.")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.error("Please try again with different parameters or check your PDF file.")
    else:
        st.info("Upload a PDF and click 'Generate MCQs' to start!")

if __name__ == "__main__":
    main()