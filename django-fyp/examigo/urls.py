from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_document, name='upload_document'),
    path('generate-quiz/<int:document_id>/', views.generate_quiz, name='generate_quiz'),
    path('take-quiz/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('submit-quiz/<int:quiz_id>/', views.submit_quiz, name='submit_quiz'),
    path('results/<int:attempt_id>/', views.view_results, name='view_results'),
    path('login/', auth_views.LoginView.as_view(template_name='examigo/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('register/', views.register, name='register'),

]

urlpatterns += [
    path('chat/<int:document_id>/', views.document_chat, name='document_chat'),
    path('chat/message/<int:chat_id>/', views.chat_message, name='chat_message'),
]