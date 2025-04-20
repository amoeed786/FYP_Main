from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.conf import settings

import os
import logging

from .models import Document, Quiz, Question, Attempt, Answer, DocumentChat, ChatMessage
from .forms import DocumentForm, QuizGenerationForm, AnswerForm

# Import your services that will handle the AI functionality
from .services.pdf_processor import process_pdf
from .services.question_generator import generate_questions
from .services.answer_evaluator import evaluate_answer
from .services.document_processor import process_document_for_chat, generate_ai_response

logger = logging.getLogger(__name__)

def home(request):
    """
    Home page view that shows recent quizzes and provides navigation.
    For logged-in users, it shows their documents and quizzes.
    """
    if request.user.is_authenticated:
        documents = Document.objects.filter(uploaded_by=request.user).order_by('-uploaded_at')[:5]
        recent_quizzes = Quiz.objects.filter(document__uploaded_by=request.user).order_by('-created_at')[:5]
        recent_attempts = Attempt.objects.filter(user=request.user).order_by('-started_at')[:5]
        
        context = {
            'documents': documents,
            'recent_quizzes': recent_quizzes,
            'recent_attempts': recent_attempts,
        }
    else:
        context = {}
    
    return render(request, 'examigo/home.html', context)

def register(request):
    """
    User registration view that creates new accounts.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    
    return render(request, 'examigo/register.html', {'form': form})

# Replace your existing upload_document function in examigo/views.py with this one

@login_required
def upload_document(request):
    """
    View for handling PDF document uploads.
    Processes the uploaded PDF to prepare it for question generation and chat functionality.
    """
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            # Create the document but don't save yet
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            
            # Get the file path for processing
            file_path = os.path.join(settings.MEDIA_ROOT, str(document.file))
            
            # Process the PDF for quiz generation
            process_pdf(document)
            
            # Process document for chat functionality
            try:
                process_document_for_chat(file_path, document.id)
                messages.success(request, f'Document "{document.title}" uploaded successfully and prepared for AI chat.')
            except Exception as e:
                logger.error(f"Error processing document for chat: {str(e)}")
                messages.warning(request, f'Document uploaded for quizzes, but chat processing failed: {str(e)}')
            
            return redirect('generate_quiz', document_id=document.id)
    else:
        form = DocumentForm()
    
    return render(request, 'examigo/upload_document.html', {'form': form})
@login_required
def generate_quiz(request, document_id):
    """
    View for configuring and generating a quiz from an uploaded document.
    """
    document = get_object_or_404(Document, id=document_id, uploaded_by=request.user)
    
    if request.method == 'POST':
        form = QuizGenerationForm(request.POST)
        if form.is_valid():
            # Create the quiz
            quiz = Quiz(
                title=form.cleaned_data['title'],
                document=document,
                difficulty=form.cleaned_data['difficulty'],
                bloom_level=form.cleaned_data['bloom_level']
            )
            quiz.save()
            
            # Generate questions using your AI service
            topic = form.cleaned_data['topic']
            num_questions = form.cleaned_data['num_questions']
            question_type = form.cleaned_data['question_type']
            
            # This calls your AI service to generate questions
            questions_data = generate_questions(
                document, 
                topic, 
                num_questions, 
                quiz.difficulty, 
                question_type, 
                quiz.bloom_level
            )
            
            # Create Question objects for each generated question
            for q_data in questions_data:
                Question.objects.create(
                    quiz=quiz,
                    text=q_data['question'],
                    ideal_answer=q_data['ideal_answer']
                )
            
            messages.success(request, f'Quiz "{quiz.title}" generated successfully with {num_questions} questions.')
            return redirect('take_quiz', quiz_id=quiz.id)
    else:
        # Suggest a default title based on the document
        suggested_title = f"Quiz on {document.title}"
        form = QuizGenerationForm(initial={'title': suggested_title})
    
    return render(request, 'examigo/generate_quiz.html', {
        'form': form,
        'document': document
    })

@login_required
def take_quiz(request, quiz_id):
    """
    View for displaying and taking a quiz.
    """
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check if the user has access to this quiz
    if quiz.document.uploaded_by != request.user:
        messages.error(request, "You don't have permission to access this quiz.")
        return redirect('home')
    
    # Check if there's an existing incomplete attempt
    existing_attempt = Attempt.objects.filter(
        quiz=quiz,
        user=request.user,
        completed_at__isnull=True
    ).first()
    
    if existing_attempt:
        attempt = existing_attempt
    else:
        # Create a new attempt
        attempt = Attempt.objects.create(
            quiz=quiz,
            user=request.user
        )
    
    # Get all questions for this quiz
    questions = quiz.questions.all()
    
    # Prepare forms for each question
    answer_forms = []
    for question in questions:
        # Check if user already answered this question
        existing_answer = Answer.objects.filter(
            attempt=attempt,
            question=question
        ).first()
        
        if existing_answer:
            # Pre-populate with existing answer
            form = AnswerForm(instance=existing_answer, prefix=f'q{question.id}')
        else:
            # Create blank form
            form = AnswerForm(prefix=f'q{question.id}')
        
        answer_forms.append((question, form))
    
    return render(request, 'examigo/take_quiz.html', {
        'quiz': quiz,
        'attempt': attempt,
        'answer_forms': answer_forms
    })

@login_required
def submit_quiz(request, quiz_id):
    """
    Handle quiz submission and evaluate answers.
    """
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Find the user's attempt
    attempt = get_object_or_404(Attempt, quiz=quiz, user=request.user, completed_at__isnull=True)
    questions = quiz.questions.all()
    
    if request.method == 'POST':
        # Process each question's answer
        total_score = 0
        total_possible = len(questions) * 10  # Assuming 10 points max per question
        
        for question in questions:
            form_prefix = f'q{question.id}'
            
            # Get the form data for this question
            form = AnswerForm(request.POST, prefix=form_prefix)
            
            if form.is_valid():
                answer_text = form.cleaned_data['text']
                
                # Check if an answer already exists
                existing_answer = Answer.objects.filter(
                    attempt=attempt,
                    question=question
                ).first()
                
                if existing_answer:
                    # Update existing answer
                    existing_answer.text = answer_text
                    answer = existing_answer
                else:
                    # Create new answer
                    answer = Answer(
                        attempt=attempt,
                        question=question,
                        text=answer_text
                    )
                
                # Evaluate the answer using your AI service
                evaluation = evaluate_answer(question.text, question.ideal_answer, answer_text)
                
                # Update the answer with evaluation results
                answer.score = evaluation['grade']
                answer.feedback = evaluation['feedback']
                answer.save()
                
                total_score += answer.score
        
        # Mark the attempt as complete
        attempt.completed_at = timezone.now()
        attempt.score = total_score
        attempt.save()
        
        messages.success(request, f'Quiz submitted! Your score: {total_score}/{total_possible}')
        return redirect('view_results', attempt_id=attempt.id)
    
    # If not a POST request, redirect to the quiz taking page
    return redirect('take_quiz', quiz_id=quiz.id)

@login_required
def view_results(request, attempt_id):
    """
    View for displaying quiz results after submission.
    """
    attempt = get_object_or_404(Attempt, id=attempt_id, user=request.user)
    quiz = attempt.quiz
    
    # Get all answers with their questions
    answers = Answer.objects.filter(attempt=attempt).select_related('question')
    
    # Calculate percentage score
    max_possible = len(answers) * 10  # Assuming 10 points max per question
    if max_possible > 0:
        percentage = (attempt.score / max_possible) * 100
    else:
        percentage = 0
    
    return render(request, 'examigo/results.html', {
        'attempt': attempt,
        'quiz': quiz,
        'answers': answers,
        'percentage': percentage
    })

# Add these views to examigo/views.py

@login_required
def document_chat(request, document_id):
    """
    Display the chat interface for a specific document.
    """
    document = get_object_or_404(Document, id=document_id, uploaded_by=request.user)
    
    # Create or get chat session
    chat, created = DocumentChat.objects.get_or_create(
        document=document,
        user=request.user,
        defaults={'title': f"Chat about {document.title}"}
    )
    
    # Get existing messages
    messages_list = chat.messages.all().order_by('timestamp')
    
    return render(request, 'examigo/document_chat.html', {
        'document': document,
        'chat': chat,
        'messages': messages_list
    })

@login_required
def chat_message(request, chat_id):
    """
    Handle new chat messages via AJAX.
    """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        chat = get_object_or_404(DocumentChat, id=chat_id, user=request.user)
        user_message = request.POST.get('message', '').strip()
        
        if user_message:
            # Save user message
            ChatMessage.objects.create(
                chat=chat,
                is_user=True,
                content=user_message
            )
            
            # Generate AI response
            try:
                ai_response = generate_ai_response(chat.document.id, user_message)
                
                # Save AI response
                ai_message = ChatMessage.objects.create(
                    chat=chat,
                    is_user=False,
                    content=ai_response
                )
                
                return JsonResponse({
                    'status': 'success',
                    'message': ai_message.content,
                    'timestamp': ai_message.timestamp.strftime('%H:%M')
                })
            except Exception as e:
                logger.error(f"Error in chat message: {str(e)}")
                return JsonResponse({
                    'status': 'error',
                    'message': f"Error generating response: {str(e)}"
                }, status=500)
        
        return JsonResponse({'status': 'error', 'message': 'Message cannot be empty'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=405)