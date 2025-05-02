# examigo/decorators.py
from django.contrib.auth.decorators import user_passes_test

def student_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.role == 'student')(view_func)

def teacher_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.role == 'teacher')(view_func)
