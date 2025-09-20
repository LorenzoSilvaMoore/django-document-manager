"""
URL Configuration for django-document-manager project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Add your app URLs here when needed
    # path('documents/', include('django_document_manager.urls')),
]