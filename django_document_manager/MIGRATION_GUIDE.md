"""
Migration-Safe BaseDocumentOwnerModel Usage Guide
================================================

This guide demonstrates how to use the updated BaseDocumentOwnerModel
that handles migrations gracefully without requiring manual interventions.

Key Improvements:
- No callable defaults that cause Django migration issues
- Automatic UUID generation on save for existing and new instances
- Built-in data population management command
- Graceful handling of instances without UUIDs

Example: Adding BaseDocumentOwnerModel to an existing model with data
=====================================================================

# Before: Existing model with data
class Company(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    
    def __str__(self):
        return self.name

# After: Adding document ownership capability
from django_document_manager.models import BaseDocumentOwnerModel

class Company(BaseDocumentOwnerModel):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    
    def __str__(self):
        return self.name
    
    def get_display_name(self):
        return f"{self.name} ({self.email})"

Migration Process:
1. Change your model to inherit from BaseDocumentOwnerModel
2. Run: python manage.py makemigrations
   - This will create a standard migration adding the document_owner_uuid field
   - No manual migration needed!
3. Run: python manage.py migrate
4. Run: python manage.py populate_document_owner_uuids
   - This populates UUIDs for existing instances
5. Done! All existing instances now have UUIDs

Usage Examples:
==============

# Create a new company (gets UUID automatically)
company = Company.objects.create(name="ACME Corp", email="info@acme.com")
print(company.document_owner_uuid)  # Automatically generated

# Existing company without UUID
existing_company = Company.objects.get(name="Old Company")
print(existing_company.document_owner_uuid)  # Might be None initially

# Ensure UUID exists (will save if needed)
uuid = existing_company.ensure_document_owner_uuid()
print(uuid)  # Now guaranteed to have a UUID

# Get documents (works even if no UUID initially)
documents = existing_company.get_documents()  # Returns empty queryset if no UUID

# After save, UUID is available
existing_company.save()  # UUID generated automatically
documents = existing_company.get_documents()  # Now works normally

Command Usage:
=============

# Populate UUIDs for all BaseDocumentOwnerModel subclasses
python manage.py populate_document_owner_uuids

# Populate UUIDs for specific model
python manage.py populate_document_owner_uuids --model myapp.Company

# Dry run to see what would be updated
python manage.py populate_document_owner_uuids --dry-run

# Process in smaller batches for large datasets
python manage.py populate_document_owner_uuids --batch-size 50

# Verbose output
python manage.py populate_document_owner_uuids --verbose

Integration with Document Management:
====================================

# Create document for a company
company = Company.objects.get(name="ACME Corp")

# This works even if company doesn't have UUID yet
# (UUID will be generated automatically when creating the document)
document = Document.create_with_file(
    owner=company,
    file=uploaded_file,
    document_type="contract",
    title="Service Agreement"
)

# Get all documents for company
all_docs = company.get_documents()

# Get specific document types
contracts = company.get_documents_by_type("contract")

# Get recent documents
recent = company.get_recent_documents(limit=5)

Error Handling:
==============

The new implementation includes robust error handling:

1. UUID generation with uniqueness checks and retry logic
2. Graceful degradation for instances without UUIDs
3. Comprehensive logging for troubleshooting
4. Validation errors with clear messages

Performance Considerations:
=========================

1. UUID7 provides time-based ordering for efficient queries
2. Built-in db_index=True for optimal query performance
3. Batch processing in management command for large datasets
4. Minimal overhead - UUIDs only generated when needed

Best Practices:
==============

1. Run populate_document_owner_uuids after adding BaseDocumentOwnerModel inheritance
2. Use ensure_document_owner_uuid() when you need to guarantee UUID existence
3. Override get_display_name() in your models for better user experience
4. Monitor logs during UUID population for any issues
5. Use --dry-run first to preview changes on production systems

Troubleshooting:
===============

Q: Migration fails with "Callable default on unique field"
A: This shouldn't happen with the new implementation. If it does, ensure you're using the updated BaseDocumentOwnerModel without callable defaults.

Q: Some instances don't get UUIDs
A: Run the populate_document_owner_uuids command. Check logs for any errors during UUID generation.

Q: Performance issues with large datasets
A: Use smaller --batch-size in the management command. Consider running during off-peak hours.

Q: get_documents() returns nothing for existing instances
A: The instance might not have a UUID yet. Call ensure_document_owner_uuid() or save() the instance.
"""