# Handling Circular Dependencies with Django Document Manager

## The Problem

Django Document Manager can cause circular dependency issues when:

1. You define models that inherit from `BaseDocumentOwnerModel` in the same app where you have other models that reference the User model
2. Your app's migrations depend on `auth` (User model) and django-document-manager migrations also depend on `auth`
3. Django migration system detects a circular dependency and fails

## Error Example

```
django.db.migrations.exceptions.CircularDependencyError: myapp.0001_initial, django_document_manager.0001_initial
```

## Solutions

### Solution 1: Separate Apps (Recommended)

The cleanest solution is to separate your document-owning models into a dedicated app:

```
myproject/
├── accounts/          # User-related models
│   ├── models.py     # User extensions, profiles
│   └── migrations/
├── companies/         # Document owners
│   ├── models.py     # Company(BaseDocumentOwnerModel)
│   └── migrations/
└── documents/         # Document-related logic
    ├── models.py     # Custom document models if needed
    └── migrations/
```

**accounts/models.py:**
```python
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    # User extensions
    pass
```

**companies/models.py:**
```python
from django_document_manager.models import BaseDocumentOwnerModel

class Company(BaseDocumentOwnerModel):
    name = models.CharField(max_length=200)
    
    def get_display_name(self):
        return self.name
```

### Solution 2: Use Staged Migration Approach

If you must keep everything in one app, use the staged migration approach:

#### Step 1: Install django-document-manager with staged migrations

```bash
# Install dependencies first
pip install git+https://github.com/LorenzoSilvaMoore/django-crud-audit.git@main
pip install git+https://github.com/LorenzoSilvaMoore/django-catalogs.git@main
pip install git+https://github.com/LorenzoSilvaMoore/django-document-manager.git@main

# Use the special migration command to avoid circular dependencies
python manage.py migrate_document_manager --skip-user-deps
```

#### Step 2: Create your models

**models.py:**
```python
from django.contrib.auth.models import AbstractUser
from django_document_manager.models import BaseDocumentOwnerModel

class CustomUser(AbstractUser):
    pass

class Company(BaseDocumentOwnerModel):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    
    def get_display_name(self):
        return self.name
```

#### Step 3: Create and run your app migrations

```bash
python manage.py makemigrations myapp
python manage.py migrate myapp
```

#### Step 4: Complete django-document-manager migration

```bash
python manage.py migrate django_document_manager 0002
```

### Solution 3: Manual Migration Dependencies

If you need fine control, manually specify migration dependencies:

**myapp/migrations/0001_initial.py:**
```python
class Migration(migrations.Migration):
    initial = True
    
    dependencies = [
        # Depend on django-document-manager's first migration only
        ('django_document_manager', '0001_initial'),
    ]
    
    # Your operations here...
```

**myapp/migrations/0002_add_user_refs.py:**
```python
class Migration(migrations.Migration):
    dependencies = [
        ('myapp', '0001_initial'),
        # Now depend on the user relationships migration
        ('django_document_manager', '0002_add_user_relationships'),
    ]
    
    # Add user foreign keys here...
```

### Solution 4: Use RunPython for Complex Cases

For very complex scenarios, use `RunPython` to handle model creation programmatically:

```python
from django.db import migrations

def create_document_owners(apps, schema_editor):
    """
    Programmatically create document owners after all models exist
    """
    Company = apps.get_model('myapp', 'Company')
    Document = apps.get_model('django_document_manager', 'Document')
    
    # Create relationships or migrate data here
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('django_document_manager', '0002_add_user_relationships'),
        ('myapp', '0001_initial'),
    ]
    
    operations = [
        migrations.RunPython(create_document_owners),
    ]
```

## Best Practices

### 1. App Structure
```
# Good: Separated concerns
myproject/
├── users/                 # Authentication only
├── organizations/         # Document owners only  
├── documents/            # Document business logic
└── core/                 # Shared utilities

# Avoid: Everything in one app
myproject/
└── myapp/                # Users + Documents + Business Logic
```

### 2. Model Design

**Good:**
```python
# organizations/models.py
class Company(BaseDocumentOwnerModel):
    name = models.CharField(max_length=200)
    
# users/models.py  
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company = models.ForeignKey('organizations.Company', on_delete=models.CASCADE)
```

**Avoid:**
```python
# myapp/models.py - Creates circular dependencies
class CustomUser(AbstractUser):
    pass
    
class Company(BaseDocumentOwnerModel):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # Circular!
```

### 3. Migration Order

Always migrate in this order:
1. `django_document_manager` (base models)
2. Your document owner models
3. Any models that reference both users and document owners
4. Complete `django_document_manager` user relationships

### 4. Testing Migration Strategy

Test your migration strategy:

```bash
# Test with fresh database
rm db.sqlite3
python manage.py migrate_document_manager --dry-run
python manage.py migrate_document_manager
python manage.py makemigrations
python manage.py migrate
```

## Debugging Circular Dependencies

### Check Migration Dependencies
```bash
python manage.py showmigrations --plan
```

### Visualize Dependencies
```bash
# Install django-extensions
pip install django-extensions

# Generate dependency graph
python manage.py graph_models -a -g -o models.png
```

### Use the Debugging Command
```bash
python manage.py migrate_document_manager --app myapp --dry-run
```

## Recovery from Circular Dependency Errors

If you're already stuck with circular dependencies:

### Option 1: Reset Migrations
```bash
# Backup your data first!
python manage.py dumpdata > backup.json

# Remove problematic migrations
rm myapp/migrations/0001_initial.py
rm django_document_manager/migrations/0001_initial.py  # if you modified it

# Recreate migrations
python manage.py makemigrations django_document_manager
python manage.py makemigrations myapp
python manage.py migrate
```

### Option 2: Manual Dependency Editing
Edit migration files to break the circular dependency by removing some dependencies temporarily, then add them back in later migrations.

## Production Deployment

For production deployments with existing data:

1. **Test thoroughly** in a staging environment
2. **Backup your database** before migration
3. **Use staged deployment** if you have complex dependencies
4. **Monitor migration performance** for large datasets

```bash
# Production migration with monitoring
python manage.py migrate --verbosity=2 | tee migration.log
```