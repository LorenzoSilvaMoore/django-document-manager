# Installation Guide for Django Document Manager with Private Dependencies

## The Problem
Django Document Manager depends on private GitHub repositories (django-crud-audit and django-catalogs). When pip tries to install the package, it fails to resolve these private dependencies.

## Solution: Install Dependencies in Correct Order

### Option 1: Manual Installation (Recommended)

```bash
# 1. Install private dependencies first (requires GitHub access)
pip install git+https://github.com/LorenzoSilvaMoore/django-crud-audit.git@main
pip install git+https://github.com/LorenzoSilvaMoore/django-catalogs.git@main

# 2. Install other dependencies from your requirements.txt (excluding the problematic lines)
pip install django>=5.2,<6.0
pip install djangorestframework>=3.15
pip install django-widget-tweaks>=1.5.0
pip install django-modeltranslation>=0.18.0
pip install django-allauth[socialaccount]>=0.60.1
pip install argon2-cffi>=23.1.0
pip install pgvector>=0.3.6
pip install psycopg[binary,pool]>=3.1.18
pip install gunicorn>=21.2
pip install dotenv>=0.9.9
pip install celery>=5.5
pip install django-celery-results

# 3. Install django-document-manager
pip install git+https://github.com/LorenzoSilvaMoore/django-document-manager.git@main

# 4. Install django-iso-3166 if needed
pip install git+https://github.com/LorenzoSilvaMoore/django-iso-3166.git@main
```

### Option 2: Split Requirements Files

Create three separate requirements files:

**requirements-private.txt:**
```
git+https://github.com/LorenzoSilvaMoore/django-crud-audit.git@main
git+https://github.com/LorenzoSilvaMoore/django-catalogs.git@main
git+https://github.com/LorenzoSilvaMoore/django-document-manager.git@main
git+https://github.com/LorenzoSilvaMoore/django-iso-3166.git@main
```

**requirements-public.txt:**
```
django>=5.2,<6.0
djangorestframework>=3.15
django-widget-tweaks>=1.5.0
django-modeltranslation>=0.18.0
django-allauth[socialaccount]>=0.60.1
argon2-cffi>=23.1.0
pgvector>=0.3.6
psycopg[binary,pool]>=3.1.18
gunicorn>=21.2
dotenv>=0.9.9
celery>=5.5
django-celery-results
```

**Install command:**
```bash
pip install -r requirements-public.txt
pip install -r requirements-private.txt
```

### Option 3: Use Environment Variables for GitHub PAT

Set up your GitHub Personal Access Token:

```bash
# Set environment variable
export GITHUB_PAT="your_github_pat_here"

# Then use in requirements
git+https://${GITHUB_PAT}@github.com/LorenzoSilvaMoore/django-crud-audit.git@main
```

## Django Settings Configuration

Add to your `INSTALLED_APPS` in the correct order:

```python
INSTALLED_APPS = [
    # ... your other apps
    'django_crud_audit',      # Must come first
    'django_catalogs',        # Must come second  
    'django_document_manager', # Must come after dependencies
    'django_iso_3166',        # Optional, if using
]
```

## Verification

Test that everything is installed correctly:

```python
# Test imports
try:
    from django_crud_audit.models import BaseModel
    from django_catalogs.models import BaseCatalogModel
    from django_document_manager.models import Document, DocumentType
    print("✅ All dependencies installed correctly")
except ImportError as e:
    print(f"❌ Import error: {e}")
```