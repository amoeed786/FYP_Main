from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser


# examigo/models.py
from django.conf import settings
from django.db import models
class SemesterPlan(models.Model):
    """
    Represents a teacher's semester-long plan for a specific document (book/course material).
    """
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="semester_plans"
    )
    document = models.ForeignKey(
        'examigo.Document',
        on_delete=models.CASCADE,
        related_name="semester_plans"
    )
    title = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Add this field to store the generated content
    content = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.teacher.username})"
class CustomUser(AbstractUser):
    """
    Extends Django's AbstractUser to add a 'role' field.
    """
    ROLE_STUDENT = 'student'
    ROLE_TEACHER = 'teacher'
    ROLE_CHOICES = [
        (ROLE_STUDENT, 'Student'),
        (ROLE_TEACHER, 'Teacher'),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT,
        help_text="Designates whether the user is a student or teacher",
    )


class Document(models.Model):
    """Model for uploaded PDF documents"""
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='documents'
    )

    def __str__(self):
        return self.title


class Quiz(models.Model):
    """Model for generated quizzes"""
    title = models.CharField(max_length=255)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='quizzes')
    created_at = models.DateTimeField(auto_now_add=True)
    difficulty = models.CharField(
        max_length=20,
        choices=[('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard')]
    )
    bloom_level = models.CharField(
        max_length=20,
        choices=[
            ('Remember', 'Remember'),
            ('Understand', 'Understand'),
            ('Apply', 'Apply'),
            ('Analyze', 'Analyze'),
            ('Evaluate', 'Evaluate'),
            ('Create', 'Create'),
        ]
    )
    time_limit = models.IntegerField(default=0)  # 0 means no time limit


    def __str__(self):
        return f"{self.title} ({self.difficulty})"


class Question(models.Model):
    """Model for quiz questions"""
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    ideal_answer = models.TextField()

    def __str__(self):
        return self.text[:50]


class Attempt(models.Model):
    """Model for quiz attempts by users"""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
    total_possible = models.FloatField(default=0)

    def __str__(self):
        return f"{self.user.username}'s attempt on {self.quiz.title}"
    
    @property
    def time_taken(self):
        """Calculate time taken for the attempt in HH:MM:SS format"""
        if self.started_at and self.completed_at:
            time_diff = self.completed_at - self.started_at
            hours, remainder = divmod(time_diff.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        return None
    
    @property
    def time_taken_minutes(self):
        """Calculate time taken in minutes for charts"""
        if self.started_at and self.completed_at:
            time_diff = self.completed_at - self.started_at
            return time_diff.total_seconds() / 60
        return 0


class Answer(models.Model):
    """Model for user answers to questions"""
    attempt = models.ForeignKey(Attempt, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.TextField()
    score = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Answer to {self.question}"


class DocumentChat(models.Model):
    """
    Represents a chat session for a specific document.
    """
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chat_sessions')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chats'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=200, default="Chat Session")

    def __str__(self):
        return f"Chat about {self.document.title}"


class ChatMessage(models.Model):
    """
    Represents a single message in a chat session.
    """
    chat = models.ForeignKey(DocumentChat, on_delete=models.CASCADE, related_name='messages')
    is_user = models.BooleanField(default=True)  # True if from user, False if from AI
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        sender = "User" if self.is_user else "AI"
        return f"{sender} message at {self.timestamp}"