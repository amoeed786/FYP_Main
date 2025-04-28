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
    path('logout/', auth_views.LogoutView.as_view(next_page='login', http_method_names=['get', 'post']), name='logout'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register')

]

urlpatterns += [
    path('chat/<int:document_id>/', views.document_chat, name='document_chat'),
    path('chat/message/<int:chat_id>/', views.chat_message, name='chat_message'),
]