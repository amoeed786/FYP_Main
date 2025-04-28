from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')

     # Add these fields with custom related_name attributes
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='examigo_user_set'  # Custom related_name
    )
    
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='examigo_user_set'  # Custom related_name
    )
    
    def is_student(self):
        return self.user_type == 'student'
    
    def is_teacher(self):
        return self.user_type == 'teacher'
    
class Document(models.Model):
    """Model for uploaded PDF documents"""
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.title

class Quiz(models.Model):
    """Model for generated quizzes"""
    title = models.CharField(max_length=255)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    difficulty = models.CharField(max_length=20,
                                 choices=[('Easy', 'Easy'),
                                          ('Medium', 'Medium'),
                                          ('Hard', 'Hard')])
    bloom_level = models.CharField(max_length=20,
                                  choices=[('Remember', 'Remember'),
                                           ('Understand', 'Understand'),
                                           ('Apply', 'Apply'),
                                           ('Analyze', 'Analyze'),
                                           ('Evaluate', 'Evaluate'),
                                           ('Create', 'Create')])
    
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
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s attempt on {self.quiz.title}"

class Answer(models.Model):
    """Model for user answers to questions"""
    attempt = models.ForeignKey(Attempt, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.TextField()
    score = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"Answer to {self.question}"
    
# In models.py
# Add these to examigo/models.py (at the end of the file)

class DocumentChat(models.Model):
    """
    Represents a chat session for a specific document.
    """
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chat_sessions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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