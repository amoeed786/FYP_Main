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
    path('logout/', auth_views.LogoutView.as_view(next_page='login', http_method_names=['get', 'post']), name='logout'),
    path('register/', views.register, name='register'),
   

]

urlpatterns += [
    path('document/<int:document_id>/generate-semester-plan/', views.generate_semester_plan_view, name='generate_semester_plan'),
    path('plan/<int:pk>/', views.semester_plan_detail, name='semester_plan_detail'),
    path('chat/<int:document_id>/', views.document_chat, name='document_chat'),
    path('chat/message/<int:chat_id>/', views.chat_message, name='chat_message'),
    path('document/<int:pk>/', views.document_detail, name='document_for_teacher'),
    

]




    # … your existing patterns …
