import requests
import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings

@csrf_exempt
def generate_quiz(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            topic = data.get("topic", "General Knowledge")
            num_mcqs = int(data.get("numMCQs", 5))
            num_short_qs = int(data.get("numShortQs", 5))
            bloom_level = data.get("bloomLevel", "Understanding")  # Default to 'Understanding'

            # AI Prompt with Bloom's Taxonomy
            prompt = f"""
            Generate a quiz on the topic "{topic}" with {num_mcqs} MCQs and {num_short_qs} short questions.
            Use Bloom's Taxonomy level: **{bloom_level}** to set difficulty.
            
            Ensure the response is **only JSON**, in this format:
            {{
                "mcqs": [
                    {{"question": "...", "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, "answer": "..."}}
                ],
                "short_questions": [
                    {{"question": "..."}}
                ]
            }}
            
            Do **NOT** include explanations, code blocks, or extra formatting.
            """

            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }

            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            response_data = response.json()

            print("Groq API Full Response:", json.dumps(response_data, indent=4))

            # Extract quiz content
            quiz_content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

            if not quiz_content:
                return JsonResponse({"error": "Groq API did not return quiz data", "api_response": response_data}, status=500)

            # Remove Markdown code blocks if present
            quiz_content_cleaned = re.sub(r"```json\n(.*?)\n```", r"\1", quiz_content, flags=re.DOTALL).strip()

            print("Cleaned Quiz Content:", quiz_content_cleaned)

            try:
                quiz_data = json.loads(quiz_content_cleaned)  # Convert to valid JSON
            except json.JSONDecodeError:
                return JsonResponse({"error": "Groq API returned an invalid JSON format", "raw_response": quiz_content_cleaned}, status=500)

            return JsonResponse({"quiz": quiz_data})

        except json.JSONDecodeError as e:
            print("JSON Decode Error:", str(e))
            return JsonResponse({"error": "Invalid JSON response from Groq API"}, status=500)
        except Exception as e:
            print("Error:", str(e))
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)
