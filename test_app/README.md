# Test App

This directory contains test models and test cases for `django-document-manager`.

## Purpose

The `test_app` provides:
- Test models (`TestCompany`, `TestPerson`) that inherit from `BaseDocumentOwnerModel`
- Isolated database tables for testing without affecting package migrations
- Test-specific migrations that are NOT included in the package distribution

## Important Notes

⚠️ **This app is for testing only and is NOT part of the package distribution.**

### Exclusions

The `test_app` is excluded from the package via:

1. **setup.py**: `packages=find_packages(exclude=['test_app', 'test_app.*', ...])`
2. **MANIFEST.in**: `global-exclude test_app/*`
3. **.gitignore**: `test_app/migrations/0*.py` (migration files are gitignored)

### Migration Isolation

- Test app migrations are in `test_app/migrations/`
- Package migrations remain in `django_document_manager/migrations/`
- No cross-contamination between test and package migrations

## Running Tests

```bash
# Run all v0.2.7 tests
python manage.py test tests_v0_2_7

# Run all tests
python manage.py test

# Run with verbosity
python manage.py test tests_v0_2_7 --verbosity=2
```

## Test Models

### TestCompany
A simple company model for testing document ownership.

**Fields:**
- `name`: CharField (default: 'Test Company')
- Inherits all fields from `BaseDocumentOwnerModel`

### TestPerson
A simple person model for testing document ownership.

**Fields:**
- `first_name`: CharField (default: 'John')
- `last_name`: CharField (default: 'Doe')
- Inherits all fields from `BaseDocumentOwnerModel`

## Adding New Test Models

When adding new test models:

1. Add model to `test_app/models.py`
2. Run `python manage.py makemigrations test_app`
3. Run `python manage.py migrate`
4. Migration files are automatically gitignored

The test migrations will NOT be included in the package distribution.
