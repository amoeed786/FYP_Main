from django.shortcuts import redirect
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static # Redirect to your frontend
from documents.views import redirect_to_frontend  # Import the function

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/quiz/", include("quiz.urls")),
    path("api/documents/", include("documents.urls")),
    path("", redirect_to_frontend),  # Redirect root URL to index.html
]

# Serve uploaded files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

