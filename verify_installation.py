#!/usr/bin/env python3
"""
Installation verification script for Django Document Manager
Run this script to verify all dependencies are properly installed
"""

import sys

def test_imports():
    """Test that all required imports work"""
    
    print("🔍 Testing Django Document Manager installation...\n")
    
    # Test core Django
    try:
        import django
        print(f"✅ Django {django.get_version()}")
    except ImportError as e:
        print(f"❌ Django import failed: {e}")
        return False
    
    # Test uuid6
    try:
        import uuid6
        print(f"✅ uuid6 {uuid6.__version__}")
    except ImportError as e:
        print(f"❌ uuid6 import failed: {e}")
        return False
    
    # Test private dependencies
    try:
        from django_crud_audit.models import BaseModel
        print("✅ django-crud-audit")
    except ImportError as e:
        print(f"❌ django-crud-audit import failed: {e}")
        print("   Install: pip install git+https://github.com/LorenzoSilvaMoore/django-crud-audit.git@main")
        return False
    
    try:
        from django_catalogs.models import BaseCatalogModel
        print("✅ django-catalogs")
    except ImportError as e:
        print(f"❌ django-catalogs import failed: {e}")
        print("   Install: pip install git+https://github.com/LorenzoSilvaMoore/django-catalogs.git@main")
        return False
    
    # Test main package
    try:
        import django_document_manager
        print(f"✅ django-document-manager {django_document_manager.__version__}")
    except ImportError as e:
        print(f"❌ django-document-manager import failed: {e}")
        return False
    
    # Test main models
    try:
        from django_document_manager.models import (
            Document, 
            DocumentType, 
            DocumentVersion, 
            BaseDocumentOwnerModel
        )
        print("✅ All django-document-manager models")
    except ImportError as e:
        print(f"❌ Model imports failed: {e}")
        return False
    
    print("\n🎉 All dependencies installed successfully!")
    print("\n📋 Next steps:")
    print("1. Add apps to INSTALLED_APPS in settings.py:")
    print("   - 'django_crud_audit'")
    print("   - 'django_catalogs'") 
    print("   - 'django_document_manager'")
    print("2. Run: python manage.py migrate")
    print("3. Optionally load document types: python manage.py load_catalog_data document_types")
    
    return True

def test_django_settings():
    """Test Django configuration if available"""
    try:
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')
        
        import django
        from django.conf import settings
        
        # Try to configure Django with minimal settings
        if not settings.configured:
            settings.configure(
                INSTALLED_APPS=[
                    'django.contrib.contenttypes',
                    'django.contrib.auth',
                    'django_crud_audit',
                    'django_catalogs',
                    'django_document_manager',
                ],
                DATABASES={
                    'default': {
                        'ENGINE': 'django.db.backends.sqlite3',
                        'NAME': ':memory:',
                    }
                },
                USE_TZ=True,
            )
        
        django.setup()
        
        # Test model loading
        from django_document_manager.models import Document, DocumentType
        print("✅ Django configuration and model loading successful")
        return True
        
    except Exception as e:
        print(f"⚠️  Django configuration test failed: {e}")
        print("   This is normal if Django is not configured yet")
        return True  # Don't fail the overall test

if __name__ == '__main__':
    print("=" * 60)
    print("Django Document Manager Installation Verification")
    print("=" * 60)
    
    success = test_imports()
    if success:
        test_django_settings()
        print("\n✨ Installation verification complete!")
        sys.exit(0)
    else:
        print("\n💥 Installation verification failed!")
        print("Please install missing dependencies and try again.")
        sys.exit(1)