# Django Document Manager

A simple, light, and robust document manager for Django projects. This app provides models, admin integration, storage helpers and optional versioning to manage documents and their metadata without heavy dependencies.

## Features

- Lightweight Django app providing document storage and metadata.
- Models: `Document`, `Folder`, `Tag`, `DocumentVersion` (optional version history).
- Pluggable storage backends (Django's default storage or custom backends).
- Basic full-text metadata search and filtering by tags/folders.
- Optional file versioning and soft-delete support.
- Admin integration and a small, testable API for programmatic access.

## Installation

Install from PyPI (or your private index):

```bash
pip install django-document-manager
```

Add the app to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
   ...,
   'django_document_manager',
]
```

Run migrations:

```bash
python manage.py migrate
```

## Quick usage

Create and upload a document programmatically:

```python
from django.core.files.base import ContentFile
from django_document_manager.models import Document

doc = Document.objects.create(
   title='Project spec',
   description='Initial project specification',
)
doc.file.save('spec.txt', ContentFile('hello world'))
doc.save()
```

Simple query examples:

```python
# All documents in a folder
docs = Document.objects.filter(folder__slug='reports')

# Search by tag
docs = Document.objects.filter(tags__name='finance')
```

## Models (overview)

- Document: title, description, uploaded file, uploaded_by, created/modified timestamps, folder, tags, is_active (soft delete).
- Folder: hierarchical grouping for documents (optional parent relationship).
- Tag: simple tagging model with many-to-many to Document.
- DocumentVersion: stores historical versions of document files and metadata (enabled optionally).

See the code under `django_document_manager/models/` for full field details.

## Admin

The app registers concise admin views for managing documents, folders and tags. To customize the admin, extend the provided admin classes in your project.

## Configuration

Settings you may want to override:

- `DOCUMENT_MANAGER_ENABLE_VERSIONING` (bool) — enable document version history (default: False).
- `DOCUMENT_MANAGER_FILE_STORAGE` — storage backend path (defaults to Django's `DEFAULT_FILE_STORAGE`).
- `DOCUMENT_MANAGER_MAX_UPLOAD_SIZE` — maximum upload size in bytes.

Add these to your Django `settings.py` as needed.

## Tests

Run the package tests (if included) with your test runner. Example using Django's test command:

```bash
python manage.py test django_document_manager
```

## Contributing

Contributions are welcome. Please open issues for bugs or feature requests and submit pull requests for fixes.

Suggested steps for contributors:

1. Fork the repository and create a feature branch.
2. Add or update tests that cover your changes.
3. Run tests and make sure they pass.
4. Create a pull request with a clear description of the change.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Changelog

See the [CHANGELOG.md](CHANGELOG.md) for history and release notes.