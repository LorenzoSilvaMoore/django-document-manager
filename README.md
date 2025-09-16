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

### Step 1: Install Private Dependencies

This package depends on private GitHub repositories. Install these first:

```bash
# Install private dependencies with authentication
pip install git+https://github.com/LorenzoSilvaMoore/django-crud-audit.git@main
pip install git+https://github.com/LorenzoSilvaMoore/django-catalogs.git@main

# Or use the provided requirements file (requires GitHub PAT tokens)
pip install -r requirements-private.txt
```

### Step 2: Install Django Document Manager

Install from PyPI:

```bash
pip install django-document-manager
```

Or install from source:

```bash
pip install git+https://github.com/LorenzoSilvaMoore/django-document-manager.git@main
```

### Required Dependencies

The package automatically installs these public dependencies:
- `Django>=3.2,<6.0` - Django framework
- `uuid6>=2025.0.0` - For UUID7 support

The private dependencies (must be installed separately):
- `django-crud-audit>=0.2.0` - For audit trails and soft delete
- `django-catalogs>=0.2.0` - For document type catalog management

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
from django.utils import timezone

# Complete validation workflow example
document = Document.objects.get(pk=1)

# Start validation process
document.validation_status = 'pending'
document.save()

# Successful validation
document.validation_status = 'validated'
document.validated_by = request.user
document.validation_date = timezone.now()
document.validation_notes = 'All financial data verified and cross-checked'
document.validation_errors = []  # Clear any previous errors
document.save()

# Rejection workflow
document.validation_status = 'rejected'
document.validation_notes = 'Document missing required signatures on page 3'
document.validation_errors = [
    'missing_signature_ceo',
    'missing_signature_cfo',
    'incomplete_date_section'
]
document.save()

# Query documents by validation status
pending_docs = Document.objects.filter(validation_status='pending')
validated_docs = Document.objects.filter(validation_status='validated')
rejected_docs = Document.objects.filter(validation_status='rejected')
```

### 6. AI Processing Integration

```python
from decimal import Decimal

# Store AI processing results
document.ai_extracted_data = {
    'financial_summary': {
        'total_revenue': 1500000,
        'net_profit': 250000,
        'operating_expenses': 1250000
    },
    'key_dates': {
        'quarter_end': '2024-12-31',
        'report_date': '2024-01-15'
    },
    'metadata': {
        'pages_processed': 45,
        'extraction_method': 'OCR + NLP',
        'processor_version': '2.1.0'
    }
}
document.ai_confidence_score = Decimal('95.50')
document.save()

# Query by AI confidence levels
high_confidence = Document.objects.filter(ai_confidence_score__gte=90)
needs_review = Document.objects.filter(ai_confidence_score__lt=75)
ai_processed = Document.objects.exclude(ai_extracted_data={})
```

### 7. Access Control Examples

```python
# Set document access levels
document.access_level = 'confidential'
document.is_confidential = True
document.save()

# Query by access level
public_docs = Document.objects.filter(access_level='public')
confidential_docs = Document.objects.filter(is_confidential=True)
internal_docs = Document.objects.filter(access_level='internal')

# Bulk access control updates
financial_docs = Document.objects.filter(document_type__is_financial=True)
financial_docs.update(access_level='restricted', is_confidential=True)
```

## Models Overview

### Document
The core document model with comprehensive metadata and validation workflows:

**Core Fields:**
- **Ownership**: `owner_uuid`, `owner_model` - Generic foreign key to any owner model
- **Classification**: `document_type` - Link to DocumentType catalog
- **Metadata**: `title`, `description`, `expiration_date`

**Validation Workflow:**
- **`validation_status`** - Tracks document validation state:
  - `'pending'` - Pending Review (default)
  - `'validated'` - Validated and approved
  - `'rejected'` - Rejected during review
  - `'requires_update'` - Needs updates before approval
- **`validated_by`** - User who performed validation
- **`validation_date`** - When validation was completed
- **`validation_notes`** - Detailed validation notes
- **`validation_errors`** - JSON array of validation errors

**AI Processing:**
- **`ai_extracted_data`** - JSON object containing AI-extracted data
- **`ai_confidence_score`** - Decimal (0-100) indicating AI confidence level

**Access Control:**
- **`access_level`** - Controls document visibility:
  - `'public'` - Public access
  - `'internal'` - Internal team access (default)
  - `'restricted'` - Restricted access
  - `'confidential'` - Confidential access
- **`is_confidential`** - Boolean flag for confidential documents

**Audit Trail:**
- Automatic `date_created`, `date_updated`, `date_deleted` via django-crud-audit
- Soft-delete support with `date_deleted` field

### DocumentVersion
Complete file versioning system with automatic metadata computation:

**File Management:**
- **`file`** - FileField storing the actual document
- **`file_size_bytes`** - Auto-computed file size in bytes
- **`file_hash`** - Auto-computed SHA-256 hash for integrity verification
- **`mime_type`** - Auto-detected MIME type
- **`file_original_name`** - Original filename when uploaded

**Version Control:**
- **`version`** - Auto-incremented version number (atomic)
- **`is_current`** - Boolean indicating current version (unique constraint)
- **`replaced_by`** - Self-referencing FK to replacement version
- **`document_date`** - Date when document content was created/effective

**Key Features:**
- Atomic version incrementing prevents race conditions
- Automatic file metadata computation on save
- Unique constraints prevent duplicate versions
- File integrity verification via SHA-256 hashing

### DocumentType
Catalog-based document type system with validation rules:

**Catalog Integration:**
- **`name`**, **`code`**, **`description`** - Standard catalog fields from django-catalogs
- **`is_selectable`** - Whether type can be selected by users

**Document Validation:**
- **`file_extensions`** - JSON array of allowed file extensions (e.g., `[".pdf", ".docx"]`)
- **`max_file_size_mb`** - Maximum file size in megabytes
- **`requires_validation`** - Whether documents need manual validation
- **`is_financial`** - Special handling flag for financial documents

**Default Document Types:**
The package includes predefined document types:
- `'other'` - General purpose documents
- `'financial'` - Financial statements and reports
- `'tax'` - Tax documents and returns
- `'legal'` - Legal contracts and agreements
- `'business_plan'` - Business plans and strategic documents
- `'pitch_deck'` - Investor presentations
- `'bank_statement'` - Bank account statements
- `'certificate'` - Business certificates and registrations

### BaseDocumentOwnerModel
Abstract base model enabling any entity to own documents:

**Core Fields:**
- **`document_owner_uuid`** - Automatic UUID7 generation for ownership tracking

**Key Methods:**
- **`get_documents()`** - Returns queryset of owned documents
- **`get_display_name()`** - Override to provide custom display names

**Usage Example:**
```python
class Company(BaseDocumentOwnerModel):
    name = models.CharField(max_length=200)
    
    def get_display_name(self):
        return self.name

class Individual(BaseDocumentOwnerModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    def get_display_name(self):
        return f"{self.first_name} {self.last_name}"
```

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

### Migration Management

Handle circular dependencies during migration:

```bash
# Check for circular dependencies and migrate accordingly
python manage.py migrate_document_manager

# Skip user foreign keys to avoid circular dependencies
python manage.py migrate_document_manager --skip-user-deps

# Check specific app for circular dependencies
python manage.py migrate_document_manager --app myapp --dry-run
```

## Database Design

The package uses an optimized database design with careful attention to performance and data integrity:

### Table Structure
- **`dm_document`** - Main documents table with metadata and relationships
- **`dm_document_type`** - Document types catalog with validation rules  
- **`dm_document_version`** - File versions with automatic metadata computation

### Key Indexes
**Performance-Optimized Indexes:**
- **UUID7 time-based indexes** - Natural chronological ordering without separate timestamp columns
- **Composite indexes** - `(owner_uuid, document_type)` for filtered owner queries
- **File integrity indexes** - `file_hash` for duplicate detection and verification
- **Workflow indexes** - `validation_status`, `access_level` for admin and reporting queries

### Database Constraints

**Data Integrity Constraints:**
```sql
-- Unique document titles per owner (soft-delete aware)
CONSTRAINT unique_owner_document_title 
  UNIQUE(owner_uuid, title) WHERE date_deleted IS NULL

-- Unique version numbers per document (soft-delete aware)  
CONSTRAINT unique_document_version 
  UNIQUE(document, version) WHERE date_deleted IS NULL

-- Only one current version per document (soft-delete aware)
CONSTRAINT unique_document_current 
  UNIQUE(document, is_current) WHERE date_deleted IS NULL AND is_current = TRUE

-- Prevent duplicate file content per document (soft-delete aware)
CONSTRAINT unique_document_file_hash 
  UNIQUE(document, file_hash) WHERE date_deleted IS NULL
```

**Practical Implications:**
- **Document Titles**: Must be unique per owner, prevents accidental duplicates
- **Version Control**: Automatic version numbering with race-condition protection
- **File Integrity**: Same file content cannot be uploaded twice to the same document
- **Current Version**: Exactly one current version per document, automatically managed

### Query Performance Features

**UUID7 Time-Ordered Queries:**
```python
# These queries are highly optimized due to UUID7 time encoding
recent_docs = Document.objects.filter(owner_uuid=owner_uuid).order_by('-id')[:10]
docs_since = Document.get_documents_since(owner_uuid, days_ago=7)

# Range queries use UUID7 time encoding for efficiency
from datetime import datetime, timedelta
cutoff = datetime.now() - timedelta(days=30)
recent = Document.objects.filter(id__gte=uuid6.uuid7(cutoff))
```

**Soft Delete Support:**
- All models support soft deletion via `date_deleted` field
- Constraints are soft-delete aware using `WHERE date_deleted IS NULL`
- Audit trail maintained even after deletion

## API Reference

### Document Class Methods

**Document Creation:**
```python
# Create document with file in one step
Document.create_with_file(owner, file, document_type, title, description=None, **kwargs)

# Example with all parameters
document = Document.create_with_file(
    owner=company,
    file=uploaded_file,
    document_type='financial',  # Can use code string or DocumentType instance
    title='Q4 Report',
    description='Quarterly financial report',
    access_level='restricted',
    validation_status='pending'
)
```

**Time-Based Queries (UUID7 Optimization):**
```python
# Get recent documents (leverages UUID7 time ordering)
recent_docs = Document.get_recent_documents(owner_uuid, limit=10)

# Get documents from specific time period
week_docs = Document.get_documents_since(owner_uuid, days_ago=7)
month_docs = Document.get_documents_since(owner_uuid, days_ago=30)

# Natural time ordering using UUID7 primary keys
newest_first = Document.objects.filter(owner_uuid=owner_uuid).order_by('-id')
oldest_first = Document.objects.filter(owner_uuid=owner_uuid).order_by('id')
```

**Document Instance Methods:**
```python
# Version Management
new_version = document.save_new_version(file, set_current=True, document_date=date.today())
document.set_current_version(version)

# Version Access
current_version = document.get_current_version()
latest_version = document.get_latest_version()
specific_version = document.get_version(3)  # Get version 3
version_count = document.get_num_versions()
latest_version_num = document.get_latest_version_number()

# Owner Information
owner_instance = document.get_owner_instance()
owner_display = document.get_owner_display()

# Validation
is_expired = document.is_expired()  # Checks expiration_date

# Direct queries
all_versions = document.versions.all()
active_versions = document.versions.filter(date_deleted__isnull=True)
```

### DocumentVersion Methods

```python
# File size display
version.get_file_size_display()  # Returns "1.5 MB", "500 KB", etc.

# Download URL (if URL patterns are configured)
download_url = version.get_download_url()

# Metadata access
print(f"Hash: {version.file_hash}")
print(f"MIME: {version.mime_type}")
print(f"Original name: {version.file_original_name}")
print(f"Size: {version.file_size_bytes} bytes")
```

### DocumentType Catalog Methods

```python
# Standard django-catalogs methods
doc_type = DocumentType.get_by_code('financial')
default_type = DocumentType.get_default()
selectable_types = DocumentType.get_selectable()

# Validation helpers
if doc_type.requires_validation:
    # Handle validation workflow
    pass

max_size = doc_type.max_file_size_mb * 1024 * 1024  # Convert to bytes
allowed_extensions = doc_type.file_extensions  # List of extensions

# Check file compatibility
def is_file_valid(file, doc_type):
    # Check file size
    if file.size > doc_type.max_file_size_mb * 1024 * 1024:
        return False, "File too large"
    
    # Check extension
    file_ext = os.path.splitext(file.name)[1].lower()
    if file_ext not in doc_type.file_extensions:
        return False, "File type not allowed"
    
    return True, "Valid"
```

### BaseDocumentOwnerModel Methods

```python
# Get all documents owned by entity
owner_documents = owner.get_documents()

# Filter by document type
financial_docs = owner.get_documents().filter(document_type__code='financial')

# Get recent documents
recent_docs = owner.get_documents().order_by('-id')[:10]

# Custom display name
display_name = owner.get_display_name()
```

### Advanced Usage Patterns

**Validation Workflow:**
```python
# Set up validation workflow
document.validation_status = 'pending'
document.save()

# Validate document
document.validation_status = 'validated'
document.validated_by = request.user
document.validation_date = timezone.now()
document.validation_notes = 'All financial data verified and approved'
document.validation_errors = []  # Clear any previous errors
document.save()

# Reject document
document.validation_status = 'rejected'
document.validation_notes = 'Missing required signatures'
document.validation_errors = ['signature_missing', 'date_invalid']
document.save()
```

**AI Processing Integration:**
```python
# Store AI extraction results
document.ai_extracted_data = {
    'total_revenue': 1500000,
    'net_profit': 250000,
    'key_metrics': {
        'growth_rate': 15.2,
        'profit_margin': 16.7
    },
    'extracted_date': '2024-12-31',
    'currency': 'USD'
}
document.ai_confidence_score = 95.5
document.save()

# Query by AI confidence
high_confidence = Document.objects.filter(ai_confidence_score__gte=90)
needs_review = Document.objects.filter(ai_confidence_score__lt=80)
```

**Bulk Operations:**
```python
# Bulk validation
pending_docs = Document.objects.filter(validation_status='pending')
pending_docs.update(
    validation_status='validated',
    validated_by=request.user,
    validation_date=timezone.now()
)

# Bulk access level changes
confidential_docs = Document.objects.filter(document_type__is_financial=True)
confidential_docs.update(access_level='confidential', is_confidential=True)
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

## Common Usage Patterns

### Handling File Uploads

```python
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile

# Handle Django form uploads
def handle_document_upload(request, owner):
    if 'document_file' in request.FILES:
        uploaded_file = request.FILES['document_file']
        
        # Validate file type and size
        doc_type = DocumentType.get_by_code('financial')
        if uploaded_file.size > doc_type.max_file_size_mb * 1024 * 1024:
            raise ValidationError("File too large")
        
        # Create document
        document = Document.create_with_file(
            owner=owner,
            file=uploaded_file,
            document_type=doc_type,
            title=request.POST.get('title'),
            description=request.POST.get('description', '')
        )
        return document
```

### Bulk Document Processing

```python
# Process multiple documents efficiently
documents_to_validate = Document.objects.filter(
    validation_status='pending',
    document_type__requires_validation=True
)

# Bulk update with validation
for document in documents_to_validate:
    # Custom validation logic here
    if validate_document_content(document):
        document.validation_status = 'validated'
        document.validated_by = validator_user
        document.validation_date = timezone.now()
    else:
        document.validation_status = 'requires_update'
        document.validation_notes = 'Failed automated validation'

# Bulk save
Document.objects.bulk_update(
    documents_to_validate, 
    ['validation_status', 'validated_by', 'validation_date', 'validation_notes']
)
```

### Document Expiration Management

```python
from datetime import date, timedelta

# Set expiration dates
document.expiration_date = date.today() + timedelta(days=365)  # 1 year
document.save()

# Find expiring documents
expiring_soon = Document.objects.filter(
    expiration_date__lte=date.today() + timedelta(days=30),
    expiration_date__gt=date.today()
)

# Find expired documents
expired = Document.objects.filter(expiration_date__lt=date.today())

# Auto-archive expired documents
for doc in expired:
    doc.access_level = 'restricted'
    doc.validation_notes = f"Auto-archived on {date.today()}"
    doc.save()
```

## Troubleshooting

### Common Issues

**Circular Dependency Errors:**
```bash
# If you get CircularDependencyError during migration:
django.db.migrations.exceptions.CircularDependencyError: myapp.0001_initial, django_document_manager.0001_initial

# Solution 1: Use staged migration (recommended)
python manage.py migrate_document_manager --skip-user-deps
python manage.py makemigrations myapp
python manage.py migrate myapp
python manage.py migrate django_document_manager 0002

# Solution 2: Separate document owners into different app (best practice)
# See CIRCULAR_DEPENDENCY_GUIDE.md for detailed solutions
```

**Private Dependency Installation:**
```bash
# If you get "repository not found" errors, install private dependencies first:
pip install git+https://github.com/LorenzoSilvaMoore/django-crud-audit.git@main
pip install git+https://github.com/LorenzoSilvaMoore/django-catalogs.git@main

# Then install django-document-manager
pip install django-document-manager

# Alternative: Use personal access tokens in requirements-private.txt
# Replace 'your_github_pat_here' with your actual GitHub PAT
```

**Import Errors:**
```python
# Ensure dependencies are properly installed and in correct order
pip install django-crud-audit django-catalogs  # Private deps first
pip install django-document-manager            # Then this package

# Verify INSTALLED_APPS order in settings.py
INSTALLED_APPS = [
    # ... other apps
    'django_crud_audit',      # Must come before document manager
    'django_catalogs',        # Must come before document manager
    'django_document_manager',
]
```

**Version Conflicts:**
```python
# If experiencing version increment race conditions
with transaction.atomic():
    document = Document.objects.select_for_update().get(pk=document_id)
    new_version = document.save_new_version(file)
```

**File Storage Issues:**
```python
# Configure custom storage in settings.py
DOCUMENT_MANAGER_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
DOCUMENT_MANAGER_MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB

# Or use custom upload paths
def custom_upload_path(instance, filename):
    return f"custom/path/{instance.document.owner_uuid}/{filename}"

# Apply in your settings
DOCUMENT_UPLOAD_PATH_HANDLER = 'myapp.utils.custom_upload_path'
```

**Query Performance:**
```python
# Use select_related for foreign keys
documents = Document.objects.select_related(
    'document_type', 'validated_by'
).filter(owner_uuid=owner_uuid)

# Use prefetch_related for reverse foreign keys
documents = Document.objects.prefetch_related(
    'versions'
).filter(owner_uuid=owner_uuid)

# Efficient counting
doc_count = Document.objects.filter(owner_uuid=owner_uuid).count()
version_count = DocumentVersion.objects.filter(
    document__owner_uuid=owner_uuid
).count()
```

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