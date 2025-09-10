````markdown
# Django Document Manager

A comprehensive, robust document management system for Django applications. This package provides advanced document storage, versioning, validation workflows, and AI processing capabilities with enterprise-grade features like audit trails and time-ordered queries.

## Features

### Core Functionality
- **Document Storage & Metadata**: Store documents with comprehensive metadata including titles, descriptions, validation status, and access control
- **Document Versioning**: Complete file versioning system with automatic metadata computation (file size, hash, MIME type)
- **Document Types Catalog**: Flexible catalog-based document type system with validation rules, file size limits, and extension restrictions
- **Ownership System**: Generic ownership via `BaseDocumentOwnerModel` - any model can own documents
- **UUID7 Primary Keys**: Time-ordered UUIDs for optimal database performance and natural chronological queries

### Advanced Features
- **AI Processing Integration**: Built-in fields for AI-extracted data and confidence scores
- **Validation Workflows**: Multi-stage validation with status tracking, validator assignment, and detailed notes
- **Access Control**: Granular access levels (public, internal, restricted, confidential) with confidentiality flags
- **Audit Trail**: Complete audit logging via `django-crud-audit` integration with soft-delete support
- **Time-Based Queries**: Efficient date range queries leveraging UUID7 time encoding
- **Atomic Operations**: Race-condition-free version management with database-level constraints

### Admin & Management
- **Complete Admin Interface**: Ready-to-use Django admin integration for all models
- **Management Commands**: Automated cleanup of expired documents and temporary files
- **Database Optimization**: Carefully designed indexes for high-performance queries
- **File Integrity**: SHA-256 hash verification and duplicate detection

## Installation

Install from PyPI:

```bash
pip install django-document-manager
```

The package requires these dependencies (automatically installed):
- `django-crud-audit>=0.2.0` - For audit trails and soft delete
- `django-catalogs>=0.2.0` - For document type catalog management  
- `uuid6>=2025.0.0` - For UUID7 support

Add to your Django `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... your other apps
    'django_crud_audit',      # Required dependency
    'django_catalogs',        # Required dependency  
    'django_document_manager',
]
```

Run migrations:

```bash
python manage.py migrate
```

Optionally load initial document types:

```bash
python manage.py load_catalog_data document_types
```

## Quick Start

### 1. Create a Document Owner Model

Any model can own documents by inheriting from `BaseDocumentOwnerModel`:

```python
from django_document_manager.models import BaseDocumentOwnerModel

class Company(BaseDocumentOwnerModel):
    name = models.CharField(max_length=200)
    
    def get_display_name(self):
        return self.name
```

### 2. Create and Upload Documents

```python
from django.core.files.base import ContentFile
from django_document_manager.models import Document, DocumentType

# Get or create a document type
doc_type = DocumentType.get_by_code('financial')

# Create document with file
company = Company.objects.get(pk=1)
document = Document.create_with_file(
    owner=company,
    file=ContentFile(b'file content', name='report.pdf'),
    document_type=doc_type,
    title='Q4 Financial Report',
    description='Annual financial report for Q4 2024',
    access_level='restricted'
)
```

### 3. Document Versioning

```python
# Add a new version
new_file = ContentFile(b'updated content', name='report_v2.pdf')
new_version = document.save_new_version(
    file=new_file,
    set_current=True,
    document_date=date.today()
)

# Access versions
current_version = document.get_current_version()
all_versions = document.versions.all()
latest_version = document.get_latest_version()
```

### 4. Time-Based Queries (UUID7 Optimization)

```python
# Get recent documents (leverages UUID7 time ordering)
recent_docs = Document.get_recent_documents(company.document_owner_uuid, limit=10)

# Get documents from last 7 days (efficient UUID7 range query)
week_docs = Document.get_documents_since(company.document_owner_uuid, days_ago=7)

# Natural time ordering by primary key
newest_first = Document.objects.filter(owner_uuid=company.document_owner_uuid).order_by('-id')
```

### 5. Document Validation Workflow

```python
# Validation workflow
document.validation_status = 'validated'
document.validated_by = request.user
document.validation_date = timezone.now()
document.validation_notes = 'All financial data verified'
document.save()

# AI processing results
document.ai_extracted_data = {
    'total_revenue': 1500000,
    'net_profit': 250000,
    'extracted_date': '2024-12-31'
}
document.ai_confidence_score = 95.5
document.save()
```

## Models Overview

### Document
The core document model with comprehensive metadata:

- **Ownership**: `owner_uuid`, `owner_model` - Generic foreign key to any owner model
- **Classification**: `document_type` - Link to DocumentType catalog
- **Metadata**: `title`, `description`, `expiration_date`
- **Validation**: `validation_status`, `validated_by`, `validation_date`, `validation_notes`
- **AI Processing**: `ai_extracted_data` (JSON), `ai_confidence_score`
- **Access Control**: `access_level`, `is_confidential`
- **Audit**: Automatic `date_created`, `date_updated`, `date_deleted` via django-crud-audit

### DocumentVersion
File versioning with automatic metadata computation:

- **File Management**: `file`, `file_size_bytes`, `file_hash`, `mime_type`, `file_original_name`
- **Versioning**: `version` (auto-incremented), `is_current`, `replaced_by`
- **Document Reference**: `document` (foreign key)
- **Metadata**: `document_date` - when the document content was created

### DocumentType
Catalog-based document type system:

- **Catalog Fields**: `name`, `code`, `description` (from django-catalogs)
- **Validation Rules**: `file_extensions`, `max_file_size_mb`, `requires_validation`
- **Classification**: `is_financial` - for financial document handling

### BaseDocumentOwnerModel
Abstract base for any model that can own documents:

- **UUID Field**: `document_owner_uuid` - Automatic UUID7 generation
- **Methods**: `get_documents()`, `get_display_name()`

## Configuration

Optional settings in your Django `settings.py`:

```python
# Document type configuration
DOCUMENT_MANAGER_DEFAULT_DOCUMENT_TYPE_CODE = 'other'  # Default document type
DOCUMENT_MANAGER_DOCUMENT_TYPES_DIR = '/path/to/document_types'  # Custom catalog data location

# File storage (defaults to Django's DEFAULT_FILE_STORAGE)
DOCUMENT_MANAGER_FILE_STORAGE = 'myproject.storage.CustomStorage'
DOCUMENT_MANAGER_MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB in bytes
```

## Management Commands

### Document Cleanup

Automated cleanup of expired and temporary documents:

```bash
# Clean up expired documents (default: 30 days)
python manage.py cleanup_documents

# Dry run to see what would be deleted
python manage.py cleanup_documents --dry-run

# Custom expiration threshold
python manage.py cleanup_documents --days 60

# Include temporary file cleanup
python manage.py cleanup_documents --cleanup-temp
```

## Database Design

The package uses optimized database design:

### Table Structure
- `dm_document` - Main documents table
- `dm_document_type` - Document types catalog
- `dm_document_version` - File versions

### Key Indexes
- UUID7-optimized indexes for time-based queries
- Composite indexes for owner + type queries
- Hash indexes for duplicate detection
- Validation status and access level indexes

### Constraints
- Unique document titles per owner
- Unique version numbers per document  
- Unique current version per document
- Unique file hashes per document (prevents duplicates)

## API Reference

### Document Class Methods

```python
# Creation
Document.create_with_file(owner, file, document_type, title, **kwargs)

# Time-based queries
Document.get_recent_documents(owner_uuid, limit=10)
Document.get_documents_since(owner_uuid, days_ago=7)

# Instance methods
document.save_new_version(file, set_current=True, **kwargs)
document.get_current_version()
document.get_latest_version()
document.get_version(n)
document.is_expired()
document.get_owner_instance()
```

### DocumentType Catalog Methods

```python
# From django-catalogs
DocumentType.get_by_code('financial')
DocumentType.get_default()
DocumentType.get_selectable()
```

## Testing

Run the test suite:

```bash
python manage.py test django_document_manager
```

For development:

```bash
pip install django-document-manager[dev]
pytest
```

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Add tests for new functionality
4. Ensure all tests pass: `python manage.py test`
5. Update documentation as needed
6. Submit a pull request

### Development Setup

```bash
git clone https://github.com/LorenzoSilvaMoore/django-document-manager.git
cd django-document-manager
pip install -e .[dev]
```

## Performance Notes

- **UUID7 Primary Keys**: Provide natural time ordering and eliminate the need for separate timestamp indexes
- **Optimized Queries**: Document queries by owner are highly optimized using UUID7 encoding
- **Atomic Versioning**: Version increments use database-level locking to prevent race conditions
- **Efficient Indexing**: Carefully designed composite indexes for common query patterns

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed release history.

## Requirements

- Python 3.8+
- Django 3.2+
- PostgreSQL, MySQL, or SQLite (UUID field support required)

## Links

- **GitHub**: https://github.com/LorenzoSilvaMoore/django-document-manager
- **PyPI**: https://pypi.org/project/django-document-manager/
- **Documentation**: https://github.com/LorenzoSilvaMoore/django-document-manager#readme
- **Issues**: https://github.com/LorenzoSilvaMoore/django-document-manager/issues
````