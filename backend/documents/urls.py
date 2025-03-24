from django.urls import path
from .views import chatbot_response
from .views import upload_file
from .views import extract_toc

urlpatterns = [
    path("chatbot/", chatbot_response, name="chatbot"),
    path("upload/", upload_file, name="upload_file"), 
    path("extract-toc/" ,extract_toc, name="extract_toc"), # Ensure this line exists
]
