# UUID Generation Guarantee for DocumentOwner Models

## Overview

The `BaseDocumentOwnerModel` and its associated custom manager (`DocumentOwnerManager`) and queryset (`DocumentOwnerQuerySet`) ensure that **every instance always has a `document_owner_uuid` generated**, regardless of how the instance is created.

## Protected Operations

### 1. Single Instance Creation

#### `save()` method
```python
owner = MyOwner(name="Test")
owner.save()  # UUID automatically generated
```

#### `Manager.create()`
```python
owner = MyOwner.objects.create(name="Test")  # UUID automatically generated
```

### 2. Conditional Creation

#### `get_or_create()`
```python
# On CREATE: UUID is automatically generated
owner, created = MyOwner.objects.get_or_create(name="Test")

# On GET: Existing UUID is preserved
owner, created = MyOwner.objects.get_or_create(name="Test")  # UUID unchanged
```

#### `update_or_create()`
```python
# On CREATE: UUID is automatically generated
owner, created = MyOwner.objects.update_or_create(
    name="Test",
    defaults={'description': 'Updated'}
)

# On UPDATE: Existing UUID is preserved
owner, created = MyOwner.objects.update_or_create(
    name="Test",
    defaults={'description': 'Modified'}
)  # UUID unchanged
```

### 3. Bulk Operations

#### `bulk_create()`
```python
owners = [
    MyOwner(name="Owner 1"),
    MyOwner(name="Owner 2"),
    MyOwner(name="Owner 3"),
]
MyOwner.objects.bulk_create(owners)  # UUID generated for each
```

#### `bulk_update()` - UUID Protected
```python
owners = list(MyOwner.objects.all())
for owner in owners:
    owner.document_owner_uuid = some_other_uuid  # This will be ignored

# document_owner_uuid is automatically excluded from update
MyOwner.objects.bulk_update(owners, ['document_owner_uuid', 'name'])
```

### 4. QuerySet Updates - UUID Protected

```python
# This will NOT modify UUIDs (automatically ignored with warning logged)
MyOwner.objects.filter(name="Test").update(document_owner_uuid=None)
```

## Implementation Details

### DocumentOwnerManager

Custom manager that overrides:
- `create()` - Generates UUID before creation
- `get_or_create()` - Generates UUID in defaults for new instances
- `update_or_create()` - Generates UUID in defaults for new instances, prevents UUID overwrite
- `bulk_create()` - Generates UUID for all objects before bulk insert
- `bulk_update()` - Strips `document_owner_uuid` from fields list

### DocumentOwnerQuerySet

Custom queryset that overrides:
- `update()` - Strips `document_owner_uuid` from kwargs and logs warning
- `get_or_create()` - Generates UUID in defaults for new instances
- `update_or_create()` - Generates UUID in defaults for new instances
- `bulk_create()` - Generates UUID for all objects

### BaseDocumentOwnerModel

Abstract model that:
- Uses `DocumentOwnerManager` as default manager
- Overrides `save()` to generate UUID if missing
- Implements uniqueness constraint (excluding NULL values)
- Provides `get_or_create_document_owner_uuid()` helper method

## UUID Generation Function

```python
def _generate_uuid7():
    return uuid6.uuid7()
```

Uses UUID7 for:
- Time-ordered UUIDs (sortable by creation time)
- Better database indexing performance
- Built-in chronological ordering

## Key Guarantees

1. **UUIDs are ALWAYS generated** for new instances via any method
2. **UUIDs are NEVER modified** after initial creation
3. **Bulk operations are protected** - UUIDs generated for bulk_create, ignored in bulk_update
4. **QuerySet updates are protected** - UUID modifications are silently ignored with warnings
5. **Race condition safety** - UUID uniqueness checked with retry logic in save()

## Benefits

- **No manual UUID management required** - Developers can use any Django ORM method
- **Prevents accidental UUID overwrites** - Protection at manager/queryset level
- **Consistent behavior** - All creation paths go through UUID generation logic
- **Migration-safe** - `null=True` allows existing records, UUIDs generated on first save
- **Logging** - Warns when code attempts to modify UUIDs

## Example Usage in Your Models

```python
from django_document_manager.models import BaseDocumentOwnerModel

class Company(BaseDocumentOwnerModel):
    name = models.CharField(max_length=200)
    tax_id = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'companies'

# All these operations automatically generate UUIDs:
company1 = Company.objects.create(name="Acme Corp")
company2, created = Company.objects.get_or_create(name="Test Inc")
company3, created = Company.objects.update_or_create(
    tax_id="12345",
    defaults={'name': "Updated Corp"}
)
Company.objects.bulk_create([
    Company(name="Bulk 1"),
    Company(name="Bulk 2"),
])
```

## Testing

Run the test script to verify UUID generation:

```bash
python test_uuid_generation.py
```

This tests all creation methods and protection mechanisms.
