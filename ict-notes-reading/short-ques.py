# Standard library imports
import re
import os
from dotenv import load_dotenv

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

# Short Questions Generation Functions
def generate_short_questions(llm, relevant_chunks, topic, num_questions, difficulty, question_type):
    """
    Generate Short Answer Questions using the language model.
    
    Args:
        llm: Language model instance
        relevant_chunks (list): List of relevant document chunks
        topic (str): Topic for question generation
        num_questions (int): Number of questions to generate
        difficulty (str): Difficulty level of questions
        question_type (str): Type of short questions (conceptual, analytical, etc.)
        
    Returns:
        str: Generated short questions in JSON-like format
    """
    # Combine context from chunks
    context = " ".join([
        chunk.page_content if hasattr(chunk, "page_content") else chunk.get("content", "")
        for chunk in relevant_chunks
    ])
    
    # Create system message with formatting and difficulty instructions
    system_message = ChatMessage(role="system", content=f"""You are an expert educator specializing in creating {difficulty.lower()} difficulty {question_type} short questions.
    
    Guidelines for generating questions:
    1. Questions should be clear and concise
    2. Ensure questions align with the {difficulty.lower()} difficulty level
    3. Questions should require thoughtful, brief answers
    
    Difficulty Levels:
    - Easy: Straightforward questions testing basic understanding
    - Medium: Questions requiring interpretation and moderate reasoning
    - Hard: Complex questions demanding critical analysis and deep understanding
    
    Question Types:
    - Conceptual: Testing fundamental understanding
    - Analytical: Requiring deeper reasoning and connections
    - Applied: Focusing on practical application of knowledge
    
    Format each question as a JSON-like structure:
    {{
        "question": "Describe the key characteristic of X",
        "answer_space": "____________"
    }}
    
    Provide multiple questions separated by ###""")
    
    # Create user message with generation instructions
    user_message = ChatMessage(role="user", content=f"""
    Based on the following context, generate {num_questions} {question_type} short answer questions on the topic '{topic}' with {difficulty.lower()} difficulty:
    
    Context: {context}
    
    Generate exactly {num_questions} questions in the specified JSON-like format, separated by ###.
    Ensure each question:
    - Matches the {difficulty.lower()} difficulty level
    - Relates to the {question_type} question type
    - Requires a concise, informative answer
    """)
    
    # Get response from language model
    response = llm([system_message, user_message])
    return response.content

def parse_short_questions(questions_text):
    """
    Parse generated short questions text into structured format.
    
    Args:
        questions_text (str): Raw questions text in JSON-like format
        
    Returns:
        list: List of dictionaries containing parsed questions
    """
    questions_list = []
    raw_questions = questions_text.strip().split('###')
    
    for raw_question in raw_questions:
        try:
            # Extract question using regex
            question_match = re.search(r'"question":\s*"([^"]+)"', raw_question)
            answer_space_match = re.search(r'"answer_space":\s*"([^"]*)"', raw_question)
            
            if question_match and answer_space_match:
                question = question_match.group(1)
                answer_space = answer_space_match.group(1)
                
                questions_list.append({
                    'question': question,
                    'answer_space': answer_space
                })
        except Exception as e:
            st.error(f"Error parsing question: {e}")
            continue
            
    return questions_list

def process_pdf_for_short_questions(pdf_path, query, topic, num_questions, difficulty, question_type):
    """
    Main function to process PDF and generate short questions.
    
    Args:
        pdf_path (str): Path to PDF file
        query (str): Search query for relevant content
        topic (str): Topic for question generation
        num_questions (int): Number of questions to generate
        difficulty (str): Difficulty level of questions
        question_type (str): Type of short questions
        
    Returns:
        list: List of generated short questions
    """
    documents = load_pdf(pdf_path)
    chunks = split_documents(documents)
    vector_store = create_vector_store(chunks)
    k = max(3, num_questions)
    relevant_chunks = retrieve_chunks(vector_store, query, k=k)
    questions_text = generate_short_questions(llm, relevant_chunks, topic, num_questions, difficulty, question_type)
    return parse_short_questions(questions_text)

# Initialize Language Model
llm = ChatOpenAI(
    model=OPENAI_MODEL,
    temperature=TEMPERATURE,
    openai_api_key=API_KEY
)

# Streamlit UI for Examigo
def main():
    """Main function for Streamlit UI setup and interaction"""
    # Page configuration
    st.set_page_config(page_title="Examigo", layout="wide")
    st.title("📚 Examigo: AI-Powered Short Questions Generator")
    st.markdown(
        """
        Transform your PDF notes into customized short answer questions!  
        Upload a PDF, select your preferences, and generate study materials instantly.
        """
    )
    
    # Sidebar inputs
    st.sidebar.header("📤 Upload PDF")
    uploaded_file = st.sidebar.file_uploader("Upload your study material", type="pdf")
    
    st.sidebar.header("🛠️ Customization Options")
    query = st.sidebar.text_input("Search Query", "Key concepts")
    topic = st.sidebar.text_input("Topic", "Computer Science")
    
    # Difficulty level dropdown
    difficulty = st.sidebar.selectbox(
        "Difficulty Level", 
        ["Easy", "Medium", "Hard"], 
        index=1  # Default to Medium
    )
    
    # Question type dropdown
    question_type = st.sidebar.selectbox(
        "Question Type", 
        ["Conceptual", "Analytical", "Applied"],
        index=0  # Default to Conceptual
    )
    
    num_questions = st.sidebar.slider("Number of Questions", min_value=1, max_value=10, value=5)
    
    generate_button = st.sidebar.button("Generate Questions")
    
    # Question generation and display
    if uploaded_file and generate_button:
        with st.spinner(f"Generating {num_questions} {difficulty} {question_type} Questions... Please wait."):
            try:
                # Save uploaded file
                pdf_path = f"./{uploaded_file.name}"
                with open(pdf_path, "wb") as f:
                    f.write(uploaded_file.read())
                
                # Generate Short Questions
                short_questions = process_pdf_for_short_questions(
                    pdf_path, query, topic, num_questions, difficulty, question_type
                )
                
                # Display results
                st.subheader(f"Generated {len(short_questions)} {difficulty} {question_type} Questions for *{topic}*")
                
                # Exam Paper Style Display
                st.markdown("### 📝 Question Paper")
                st.markdown(f"**Topic:** {topic} | **Difficulty:** {difficulty} | **Type:** {question_type}")
                
                for i, question in enumerate(short_questions, 1):
                    st.markdown(f"**Question {i}:** {question['question']}")
                    st.text_area(f"Answer Space for Question {i}", value=question['answer_space'], height=100, key=f"answer_{i}")
                    st.markdown("---")
                
                # Warning for fewer questions
                if len(short_questions) < num_questions:
                    st.warning(f"Note: Only {len(short_questions)} questions could be generated. Try adjusting your query or topic.")
                
                # Optional: Download functionality
                exam_content = "--- Examigo Generated Question Paper ---\n\n"
                exam_content += f"Topic: {topic}\n"
                exam_content += f"Difficulty: {difficulty}\n"
                exam_content += f"Question Type: {question_type}\n\n"
                
                for i, question in enumerate(short_questions, 1):
                    exam_content += f"Question {i}: {question['question']}\n\n"
                    exam_content += "Answer:\n\n\n"
                
                st.download_button(
                    label="📥 Download Question Paper",
                    data=exam_content,
                    file_name=f"{topic}_exam_questions.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.error("Please try again with different parameters or check your PDF file.")
    else:
        st.info("Upload a PDF and click 'Generate Questions' to start your exam preparation!")

if __name__ == "__main__":
    main()