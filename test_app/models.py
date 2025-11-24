"""
Test models for django-document-manager tests

These models are only used during testing and are NOT part of the package.
"""

from django.db import models
from django_document_manager.models import BaseDocumentOwnerModel


class TestCompany(BaseDocumentOwnerModel):
    """Test model for document ownership"""
    
    name = models.CharField(max_length=200, default='Test Company')
    
    class Meta:
        app_label = 'test_app'
        db_table = 'test_app_company'
        verbose_name = 'Test Company'
        verbose_name_plural = 'Test Companies'

    def __str__(self):
        return f"{self.name} (ID: {self.pk})"
    
    def get_display_name(self):
        return f"{self.name}"


class TestPerson(BaseDocumentOwnerModel):
    """Test model for person document ownership"""
    
    first_name = models.CharField(max_length=100, default='John')
    last_name = models.CharField(max_length=100, default='Doe')
    
    class Meta:
        app_label = 'test_app'
        db_table = 'test_app_person'
        verbose_name = 'Test Person'
        verbose_name_plural = 'Test People'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_display_name(self):
        return f"{self.first_name} {self.last_name}"
