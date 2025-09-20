#!/usr/bin/env python
"""
Quick validation test for django-document-manager v0.2.0 critical fixes

Tests the main issues found in the comprehensive test:
1. ContentType-based ownership resolution
2. UUID generation for BaseDocumentOwnerModel
3. Document versioning without typos
4. Time-based queries with proper UUID7 handling
"""

import os
import sys
import django
from django.core.files.base import ContentFile

# Setup Django environment
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_build.settings')
    django.setup()
except (ImportError, Exception):
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django_document_manager',
            ],
            USE_TZ=True,
            SECRET_KEY='test-key-only',
        )
        django.setup()

from django.db import connection, models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django_document_manager.models import Document, DocumentType


class TestCompany(models.Model):
    """Test model for document ownership"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    document_owner_uuid = models.UUIDField(
        null=True,
        blank=True,
        editable=False,
        db_index=True, 
        unique=True
    )
    
    class Meta:
        app_label = 'test_app'

    def __str__(self):
        return f"TestCompany-{self.pk}"
    
    def get_display_name(self):
        return f"Test Company {self.pk}"
    
    def get_or_create_document_owner_uuid(self):
        """Generate UUID if it doesn't exist"""
        if not self.document_owner_uuid:
            import uuid6
            self.document_owner_uuid = uuid6.uuid7()
            return self.document_owner_uuid
        return self.document_owner_uuid


def setup_database():
    """Create database tables for test models"""
    print("🔧 Setting up test database...")
    
    with connection.cursor() as cursor:
        # Create TestCompany table with document_owner_uuid field
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_app_testcompany (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                document_owner_uuid VARCHAR(36) UNIQUE NULL
            )
        """)
    
    # Create Django tables
    from django.core.management import call_command
    call_command('migrate', verbosity=0, interactive=False)
    print("✅ Database setup complete")


def test_contenttype_ownership():
    """Test ContentType-based ownership system"""
    print("\n🧪 Testing ContentType-based ownership...")
    
    # Create company with UUID
    company = TestCompany.objects.create()
    uuid = company.get_or_create_document_owner_uuid()
    company.save()
    print(f"   🏢 Created company with UUID: {uuid}")
    
    # Create document type
    doc_type = DocumentType.objects.create(
        name="Test Document Type",
        code="test_type",
        max_file_size_mb=10
    )
    
    # Create document
    test_file = ContentFile(b'Test content', name='test.txt')
    document = Document.create_with_file(
        owner=company,
        file=test_file,
        document_type=doc_type,
        title="ContentType Test Document"
    )
    
    # Verify ContentType ownership
    assert document.owner_content_type is not None
    expected_ct = ContentType.objects.get_for_model(TestCompany)
    assert document.owner_content_type == expected_ct
    assert document.owner_uuid == company.document_owner_uuid
    
    # Test owner property resolution
    resolved_owner = document.owner
    assert resolved_owner is not None
    assert resolved_owner.pk == company.pk
    assert isinstance(resolved_owner, TestCompany)
    
    print(f"   ✅ Owner resolved: {resolved_owner}")
    
    # Cleanup
    document.delete()
    company.delete()
    doc_type.delete()


def test_document_versioning():
    """Test document versioning without kwargs issue"""
    print("\n🧪 Testing document versioning...")
    
    # Setup
    company = TestCompany.objects.create()
    company.get_or_create_document_owner_uuid()
    company.save()
    
    doc_type = DocumentType.objects.create(
        name="Version Test",
        code="version_test",
        max_file_size_mb=10
    )
    
    # Create initial document
    test_file = ContentFile(b'Version 1 content', name='versioned.txt')
    document = Document.create_with_file(
        owner=company,
        file=test_file,
        document_type=doc_type,
        title="Versioning Test Document"
    )
    
    initial_version = document.get_current_version()
    assert initial_version.version == 1
    print(f"   📝 Initial version: v{initial_version.version}")
    
    # Add second version
    test_file2 = ContentFile(b'Version 2 content', name='versioned_v2.txt')
    version2 = document.save_new_version(test_file2, set_current=True)
    
    assert version2.version == 2
    assert version2.is_current is True
    print(f"   📝 Second version: v{version2.version}")
    
    # Cleanup
    document.delete()
    company.delete()
    doc_type.delete()
    
    print("   ✅ Document versioning works correctly")


def test_time_based_queries():
    """Test time-based queries without UUID7 parameter issue"""
    print("\n🧪 Testing time-based queries...")
    
    # Setup
    company = TestCompany.objects.create()
    company.get_or_create_document_owner_uuid()
    company.save()
    
    doc_type = DocumentType.objects.create(
        name="Time Test",
        code="time_test"
    )
    
    # Create some documents
    for i in range(3):
        test_file = ContentFile(f'Time test doc {i+1}'.encode(), name=f'time_{i+1}.txt')
        document = Document.create_with_file(
            owner=company,
            file=test_file,
            document_type=doc_type,
            title=f"Time Test Document {i+1}"
        )
        
    print(f"   📄 Created 3 documents")
    
    # Test recent documents query (should not crash)
    try:
        recent_docs = Document.get_documents_since(company.document_owner_uuid, days_ago=1)
        print(f"   ⏰ Retrieved {recent_docs.count()} recent documents")
    except Exception as e:
        print(f"   ❌ Query failed: {e}")
        raise
    
    # Cleanup
    Document.objects.filter(owner_uuid=company.document_owner_uuid).delete()
    company.delete()
    doc_type.delete()
    
    print("   ✅ Time-based queries work correctly")


def main():
    """Run all validation tests"""
    print("🚀 Starting django-document-manager v0.2.0 Quick Validation")
    print("=" * 65)
    
    setup_database()
    
    try:
        test_contenttype_ownership()
        test_document_versioning()
        test_time_based_queries()
        
        print("\n" + "=" * 65)
        print("✅ All validation tests PASSED!")
        print("🎉 v0.2.0 core fixes are working correctly")
        
    except Exception as e:
        print(f"\n❌ Validation FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()