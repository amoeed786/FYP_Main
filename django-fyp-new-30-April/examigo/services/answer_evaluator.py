# examigo/services/answer_evaluator.py

import os
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import ChatMessage, SystemMessage, HumanMessage
import re

# Load environment variables for API keys
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)
# Constants
GOOGLE_MODEL = "gemini-2.5-flash-preview-04-17"
TEMPERATURE = 0.3  # Lower temperature for more consistent evaluation

def evaluate_answer(question, ideal_answer, user_answer):
    """
    Evaluate a user's answer against an ideal answer.
    
    Args:
        question: The question text
        ideal_answer: The ideal answer for comparison
        user_answer: The user's submitted answer
        
    Returns:
        dict: Evaluation results including grade and feedback
    """
    # Initialize language model with lower temperature for evaluation
    llm = ChatGoogleGenerativeAI(
        model=GOOGLE_MODEL,
        temperature=TEMPERATURE,
        google_api_key=GOOGLE_API_KEY
    )
    
    # Create evaluation prompt (SystemMessage and ChatMessage format)
    evaluation_prompt = SystemMessage(
        role="system",  # This should be "system", not "user", for system prompts
        content=f"""As an educational assessment expert, evaluate the student's answer against the ideal answer.
        
        Question: {question}
        
        Ideal Answer: {ideal_answer}
        
        Student Answer: {user_answer}
        
        Evaluate this answer on a scale of 0 to 10, where:
        - 0-2: Missing most key concepts, major misconceptions
        - 3-5: Includes some relevant points but lacks depth
        - 6-8: Good understanding with minor omissions
        - 9-10: Excellent, comprehensive answer
        
        Provide your evaluation in this format:
        Grade: [0-10]
        Feedback: [Specific feedback highlighting strengths and areas for improvement]
        
        Be fair but lenient in your grading. If the student's answer captures the main concepts, even if expressed differently from the ideal answer, they should receive credit.
        """
    )
    
    # Send both the SystemMessage and the ChatMessage (for content generation)
    user_message = HumanMessage(
        role="user", 
        content="Generate evaluation based on the provided answers"
    )

    response = llm([evaluation_prompt, user_message])  # Pass both messages
    
    # If you have a response, get the content of the evaluation
    if response:
        evaluation_text = response.content.strip()
    
        # Parse the response to extract grade and feedback
        grade_match = re.search(r'Grade:\s*(\d+)', evaluation_text)
        feedback_match = re.search(r'Feedback:\s*(.*)', evaluation_text, re.DOTALL)
        
        grade = int(grade_match.group(1)) if grade_match else 0
        
        # Extract feedback, defaulting to the whole response if parsing fails
        if feedback_match:
            feedback = feedback_match.group(1).strip()
        else:
            # Remove any "Grade: X" part and use the rest as feedback
            feedback = re.sub(r'Grade:\s*\d+', '', evaluation_text).strip()

        return {
            'grade': grade,
            'feedback': feedback
        }
    else:
        raise ValueError("No response received from Gemini.")
