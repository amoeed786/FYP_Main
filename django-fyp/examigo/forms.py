# examigo/forms.py
from django import forms
from .models import Document, Answer

class DocumentForm(forms.ModelForm):
    """Form for uploading PDF documents"""
    class Meta:
        model = Document
        fields = ['title', 'file']
        
class QuizGenerationForm(forms.Form):
    """Form for configuring quiz generation parameters"""
    title = forms.CharField(max_length=255, label="Quiz Title")
    topic = forms.CharField(max_length=255, label="Specific Topic", 
                          help_text="Enter a specific topic or area to focus questions on")
    num_questions = forms.IntegerField(
        min_value=1, 
        max_value=10,
        initial=5,
        label="Number of Questions"
    )
    difficulty = forms.ChoiceField(
        choices=[('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard')],
        initial='Medium',
        label="Difficulty Level"
    )
    question_type = forms.ChoiceField(
        choices=[
            ('Conceptual', 'Conceptual'), 
            ('Analytical', 'Analytical'), 
            ('Applied', 'Applied')
        ],
        initial='Conceptual',
        label="Question Type"
    )
    bloom_level = forms.ChoiceField(
        choices=[
            ('Remember', 'Remember'),
            ('Understand', 'Understand'),
            ('Apply', 'Apply'),
            ('Analyze', 'Analyze'),
            ('Evaluate', 'Evaluate'),
            ('Create', 'Create')
        ],
        initial='Understand',
        label="Bloom's Taxonomy Level"
    )

class AnswerForm(forms.ModelForm):
    """Form for submitting answers to quiz questions"""
    class Meta:
        model = Answer
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'cols': 50})
        }
        labels = {
            'text': 'Your Answer',
        }