# examigo/services/semester_plan_generator.py

import os
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

GOOGLE_MODEL = "gemini-2.5-flash-preview-04-17"
TEMPERATURE = 0.7
def generate_semester_plan(document, num_weeks=12, course_title=None, start_date=None, end_date=None):
    """
    Use Gemini to draft a semester-long plan for this document (book).
    
    Args:
      document: your Document instance (with .title and .file.url or text)
      num_weeks: how many weeks in the semester
      course_title: optional custom course name
      start_date: start date of semester (string or date object)
      end_date: end date of semester (string or date object)
    
    Returns:
      A dict with keys: title, weeks (list of {week, objectives, topics, activities})
    """
    llm = ChatGoogleGenerativeAI(
        model=GOOGLE_MODEL,
        temperature=TEMPERATURE,
        google_api_key=GOOGLE_API_KEY
    )

    # Extract text from document for context
    # Consider using your pdf_processor here if available
    try:
        from .pdf_processor import extract_text_from_pdf
        text_context = extract_text_from_pdf(document.file.path)[:3000]
    except (ImportError, AttributeError):
        # Fallback to simple reading if pdf_processor isn't available
        text_context = document.file.read().decode("utf-8", errors="ignore")[:3000]
    
    title = course_title or document.title.replace('_', ' ').title()
    
    date_context = ""
    if start_date and end_date:
        date_context = f"The semester runs from {start_date} to {end_date}."
    
    system_message = SystemMessage(
        content=(
            f"You are an expert curriculum designer. "
            f"Create a {num_weeks}-week semester plan for a course titled '{title}' "
            f"based on this document: {text_context}\n\n"
            f"{date_context}\n\n"
            f"The semester plan should include weekly breakdowns with: "
            f"1. Learning objectives for each week "
            f"2. Key topics to cover "
            f"3. Suggested learning activities or assignments\n\n"
            f"Format your response as a structured JSON with this format:\n"
            f"{{\n"
            f"  \"title\": \"Course Title\",\n"
            f"  \"weeks\": [\n"
            f"    {{\n"
            f"      \"week\": 1,\n"
            f"      \"objectives\": [\"objective 1\", \"objective 2\"],\n"
            f"      \"topics\": [\"topic 1\", \"topic 2\"],\n"
            f"      \"activities\": [\"activity 1\", \"activity 2\"]\n"
            f"    }},\n"
            f"    // more weeks...\n"
            f"  ]\n"
            f"}}"
        )
    )
    
    human_message = HumanMessage(
        content=f"Please create a semester plan for this course material."
    )
    
    messages = [system_message, human_message]
    
    response = llm(messages)
    response_content = response.content
    
    # Extract the JSON part from the response
    try:
        # Look for JSON pattern in the response
        import re
        import json
        
        # Try to find JSON pattern in response
        json_match = re.search(r'({[\s\S]*})', response_content)
        if json_match:
            json_str = json_match.group(1)
            plan_data = json.loads(json_str)
        else:
            # If no JSON pattern found, try parsing the whole response
            plan_data = json.loads(response_content)
            
        return plan_data
    except json.JSONDecodeError:
        # Handle case where response isn't valid JSON
        return {
            "title": title,
            "error": "Failed to generate semester plan in proper format",
            "raw_response": response_content
        }