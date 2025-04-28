# examigo/services/question_generator.py

import os
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, ChatMessage, HumanMessage
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from sentence_transformers import SentenceTransformer


# Load environment variables for API keys
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# Constants
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"# For embeddings
GOOGLE_MODEL = "gemini-2.5-flash-preview-04-17"  # For generation
TEMPERATURE = 0.7

# Bloom's Taxonomy reference for the AI
BLOOM_TAXONOMY = {
    'Remember': {
        'description': 'Recalling or recognizing information',
        'verbs': ['define', 'list', 'name', 'recall', 'identify', 'label']
    },
    'Understand': {
        'description': 'Explaining ideas or concepts',
        'verbs': ['describe', 'explain', 'summarize', 'interpret', 'classify', 'paraphrase']
    },
    'Apply': {
        'description': 'Using information in new situations',
        'verbs': ['apply', 'demonstrate', 'solve', 'use', 'illustrate', 'operate']
    },
    'Analyze': {
        'description': 'Drawing connections and identifying patterns',
        'verbs': ['analyze', 'compare', 'contrast', 'differentiate', 'examine', 'investigate']
    },
    'Evaluate': {
        'description': 'Justifying a stand or decision',
        'verbs': ['evaluate', 'critique', 'defend', 'judge', 'argue', 'validate']
    },
    'Create': {
        'description': 'Generating new ideas, products, or perspectives',
        'verbs': ['create', 'design', 'develop', 'compose', 'construct', 'generate']
    }
}

def generate_questions(document, topic, num_questions, difficulty, question_type, bloom_level='Understand'):
    """
    Generate questions based on document content and specified parameters.
    
    Args:
        document: Document model object
        topic: Specific topic to focus on
        num_questions: Number of questions to generate
        difficulty: Difficulty level (Easy, Medium, Hard)
        question_type: Type of questions (Conceptual, Analytical, Applied)
        bloom_level: Bloom's Taxonomy level
        
    Returns:
        list: List of generated questions with their ideal answers
    """
    # Initialize language model
    llm = ChatGoogleGenerativeAI(
        model=GOOGLE_MODEL,
        temperature=TEMPERATURE,
        google_api_key=GOOGLE_API_KEY
    )
    
    # Load the vector store for this document
    vector_store_path = os.path.join('media', 'vector_stores', f"document_{document.id}")
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    vector_store = FAISS.load_local(vector_store_path, embeddings, allow_dangerous_deserialization=True)
    
    # Retrieve relevant chunks for the topic
    k = max(3, num_questions)  # Retrieve at least 3 chunks or more based on questions
    relevant_chunks = vector_store.similarity_search(topic, k=k)
    
    # Combine context from chunks
    context = " ".join([
        chunk.page_content if hasattr(chunk, "page_content") else chunk.get("content", "")
        for chunk in relevant_chunks
    ])
    
    # Get Bloom's Taxonomy details
    bloom_info = BLOOM_TAXONOMY.get(bloom_level, BLOOM_TAXONOMY['Understand'])
    
    # Create system message with Bloom's Taxonomy integration
    system_message = SystemMessage(role="system", content=f"""You are an expert educator creating questions based on Bloom's Taxonomy.

    Bloom's Taxonomy Level: {bloom_level}
    Cognitive Skill: {bloom_info['description']}
    
    Question Generation Guidelines:
    1. Use verbs that reflect the {bloom_level} level: {', '.join(bloom_info['verbs'])}
    2. Craft questions that encourage {bloom_info['description']}
    3. Ensure questions match {difficulty.lower()} difficulty
    4. Focus on {question_type} question exploration
    
    For each question, you must provide:
    1. The question text that will be shown to students
    2. An ideal answer that will be used for grading (be thorough)
    
    Structure each question as:
    {{
        "question": "Clear, well-formulated question",
        "bloom_level": "{bloom_level}",
        "ideal_answer": "Comprehensive ideal answer that covers all key points"
    }}
    
    Provide exactly {num_questions} questions, separated by ###""")
    
    # Create user message with generation instructions
    user_message = HumanMessage(role="user", content=f"""
    Generate {num_questions} {bloom_level} level questions about '{topic}'
    
    Context from the document:
    {context}
    
    Instructions:
    - Create exactly {num_questions} questions
    - Use {bloom_level} level cognitive skills
    - Ensure {difficulty.lower()} difficulty
    - Focus on {question_type} exploration
    - Use appropriate {bloom_level} level verbs
    - Each question must have a detailed ideal answer for grading purposes
    """)
    
    # Get response from language model
    response = llm([system_message, user_message])
    questions_text = response.content
    
    # Parse the response
    return parse_generated_questions(questions_text)

def parse_generated_questions(questions_text):
    """
    Parse the AI-generated questions into a structured format.
    
    Args:
        questions_text: Raw text response from the AI
        
    Returns:
        list: List of question dictionaries
    """
    questions_list = []
    raw_questions = questions_text.strip().split('###')
    
    import re
    
    for raw_question in raw_questions:
        if not raw_question.strip():
            continue
            
        try:
            # Extract question, bloom level, and ideal answer using regex
            question_match = re.search(r'"question":\s*"([^"]+)"', raw_question)
            bloom_level_match = re.search(r'"bloom_level":\s*"([^"]*)"', raw_question)
            ideal_answer_match = re.search(r'"ideal_answer":\s*"([^"]*)"', raw_question)
            
            if question_match and ideal_answer_match:
                question = question_match.group(1)
                ideal_answer = ideal_answer_match.group(1)
                bloom_level = bloom_level_match.group(1) if bloom_level_match else 'Understand'
                
                questions_list.append({
                    'question': question,
                    'ideal_answer': ideal_answer,
                    'bloom_level': bloom_level
                })
        except Exception as e:
            # In a real app, you'd log this error properly
            print(f"Error parsing question: {e}")
            continue
            
    return questions_list