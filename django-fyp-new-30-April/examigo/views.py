from .forms import SemesterPlanForm
from .models import SemesterPlan
from .models import CustomUser
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponse
import io
from django.http import FileResponse
from .forms import CustomUserCreationForm
import os
import csv
import logging
from .models import Document, Quiz, Question, Attempt, Answer, DocumentChat, ChatMessage
from .forms import DocumentForm, QuizGenerationForm, AnswerForm
from .services.pdf_processor import process_pdf
from .services.question_generator import generate_questions
from .services.answer_evaluator import evaluate_answer
from .services.document_processor import process_document_for_chat, generate_ai_response
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors

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
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # you can inspect user.role here
            messages.success(request, f'Account created for {user.username} as {user.get_role_display()}!')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
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
            
            if request.user.role == 'teacher':
               print(document.id)
               return redirect('document_detail', document_id=document.id)
            else:
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
    Only students can take the quiz. Teachers are not allowed to access this.
    """
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.user.role == CustomUser.ROLE_TEACHER:
        # If teacher, generate quiz file for download instead
        return download_quiz_as_file(request,quiz_id)  # You define this function

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

    if request.user.role == CustomUser.ROLE_TEACHER:
        return HttpResponseForbidden("Teachers are not allowed to submit quizzes.")
    
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

def download_quiz_as_file(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{quiz.title.replace(" ", "_")}_quiz.pdf"'
    
    # Create a buffer and document
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Create a custom style for questions and answers
    question_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        leftIndent=0,
        rightIndent=0,
        firstLineIndent=0,
        alignment=TA_LEFT,
        spaceBefore=12,
        spaceAfter=6
    )
    
    answer_style = ParagraphStyle(
        'AnswerStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=13,
        leftIndent=20,
        rightIndent=0,
        firstLineIndent=0,
        alignment=TA_LEFT,
        spaceBefore=6,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    # Build the document content
    content = []
    
    # Add title
    content.append(Paragraph(f"{quiz.title}", title_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Add quiz metadata
    content.append(Paragraph(f"<b>Document:</b> {quiz.document.title}", normal_style))
    content.append(Paragraph(f"<b>Difficulty:</b> {quiz.difficulty}", normal_style))
    content.append(Paragraph(f"<b>Bloom's Level:</b> {quiz.bloom_level}", normal_style))
    content.append(Paragraph(f"<b>Total Questions:</b> {quiz.questions.count()}", normal_style))
    content.append(Spacer(1, 0.5*inch))
    
    # Add questions and answers
    content.append(Paragraph("Questions and Answers", subtitle_style))
    content.append(Spacer(1, 0.25*inch))
    
    for i, question in enumerate(quiz.questions.all(), 1):
        # Add question text with number
        q_text = f"Question {i}: {question.text}"
        content.append(Paragraph(q_text, question_style))
        
        # Add ideal answer
        a_text = f"Ideal Answer: {question.ideal_answer}"
        content.append(Paragraph(a_text, answer_style))
        
        # Add spacer between question-answer pairs
        if i < quiz.questions.count():
            content.append(Spacer(1, 0.2*inch))
    
    # Build and save the PDF
    doc.build(content)
    
    # Get the PDF value and close buffer
    pdf_data = buffer.getvalue()
    buffer.close()
    
    # Write to response and return
    response.write(pdf_data)
    return response

def download_quiz_txt(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{quiz.title}_quiz.txt"'
    
    content = f"Quiz: {quiz.title}\nDifficulty: {quiz.difficulty}\nBloom's Level: {quiz.bloom_level}\n\n"
    for question in quiz.questions.all():
        content += f"Q: {question.text}\nA: {question.ideal_answer}\n\n"

    response.write(content)
    return response
def download_quiz_docx(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename="{quiz.title}_quiz.docx"'
    
    doc = Document()
    doc.add_heading(f"Quiz: {quiz.title}", 0)
    doc.add_paragraph(f"Difficulty: {quiz.difficulty}")
    doc.add_paragraph(f"Bloom's Level: {quiz.bloom_level}")
    
    for question in quiz.questions.all():
        doc.add_paragraph(f"Q: {question.text}")
        doc.add_paragraph(f"A: {question.ideal_answer}")
    
    doc.save(response)
    return response

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
                print("going to get")
                ai_response = generate_ai_response(chat.document.id, user_message)
                print("out to get")
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

@login_required
def document_detail(request, document_id):
    document = get_object_or_404(Document, pk=document_id, uploaded_by=request.user)
    created_plan = None
    created_weeks = None

    if request.user.role != 'teacher':
        return redirect('generate_quiz', document_id=document.id)

    # bind form to POST or leave unbound
    form = SemesterPlanForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        plan = form.save(commit=False)
        plan.teacher = request.user
        plan.document = document
        plan.save()
        created_plan = plan

        # parse JSON weeks if stored in notes
        try:
            created_weeks = json.loads(plan.notes)
        except Exception:
            created_weeks = None

        # reset form for new input
        form = SemesterPlanForm()

    return render(request, 'examigo/document_for_teacher.html', {
        'document': document,
        'plan_form': form,
        'created_plan': created_plan,
        'created_weeks': created_weeks,
    })


from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Document, SemesterPlan
from .services.semester_plan_generator import generate_semester_plan
from datetime import datetime, timedelta

@login_required
def generate_semester_plan_view(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    
    # Check if the user has permission to create plans for this document
    # Adjust this based on your permissions model
    if not (request.user.is_staff or document.uploaded_by == request.user):
        messages.error(request, "You don't have permission to create plans for this document.")
        return redirect('home')
    
    if request.method == 'POST':
        num_weeks = int(request.POST.get('num_weeks', 12))
        course_title = request.POST.get('course_title', '')
        
        # Parse dates from form
        try:
            start_date = datetime.strptime(request.POST.get('start_date'), '%Y-%m-%d').date()
            # Calculate end date based on start date and number of weeks
            end_date = start_date + timedelta(weeks=num_weeks)
        except (ValueError, TypeError):
            # If date parsing fails, use today and today + num_weeks as fallback
            start_date = datetime.now().date()
            end_date = start_date + timedelta(weeks=num_weeks)
        
        notes = request.POST.get('notes', '')
        
        if not course_title:
            course_title = document.title.replace('_', ' ').title()
        
        try:
            # Generate the semester plan
            plan_data = generate_semester_plan(
                document, 
                num_weeks=num_weeks, 
                course_title=course_title,
                start_date=start_date,
                end_date=end_date
            )
            
            # Create and save the semester plan
            semester_plan = SemesterPlan(
                teacher=request.user,
                document=document,
                title=course_title,
                start_date=start_date,
                end_date=end_date,
                notes=notes,
                content=plan_data  # Store the JSON data in the content field
            )
            semester_plan.save()
            
            messages.success(request, 'Semester plan generated successfully!')
            print(semester_plan.id)
            return redirect('semester_plan_detail', plan_id=semester_plan.id)
            
        except Exception as e:
            messages.error(request, f'Error generating semester plan: {str(e)}')
            return redirect('document_for_teacher', document_id=document_id)
    
    # For GET requests, render the form
    today = datetime.now().date()
    default_end_date = today + timedelta(weeks=12)
    
    return render(request, 'examigo/generate_semester_plan.html', {
        'document': document,
        'default_start_date': today.strftime('%Y-%m-%d'),
        'default_end_date': default_end_date.strftime('%Y-%m-%d')
    })


@login_required
def semester_plan_detail(request, plan_id):
    plan = get_object_or_404(SemesterPlan, pk=plan_id)
    
    # Check if user has permission to view this plan
    if not (request.user.is_staff or plan.teacher == request.user):
        messages.error(request, "You don't have permission to view this plan.")
        return redirect('home')
    
    return render(request, 'examigo/semester_plan_detail.html', {
        'plan': plan
    })
import json
@login_required
def semester_plan_detail(request, id):
    """
    Show the saved semester plan.
    """
    plan = get_object_or_404(SemesterPlan, pk=id, teacher=request.user)
    # parse JSON weeks if stored in notes
    try:
        weeks = json.loads(plan.notes)
    except Exception:
        weeks = None

    return render(request, 'examigo/semester_plan_detail.html', {
        'plan': plan,
        'weeks': weeks,
    })