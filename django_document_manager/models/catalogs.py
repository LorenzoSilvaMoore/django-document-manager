from pathlib import Path

from django.conf import settings

from django_document_manager.models import DocumentType

try:
    from django_catalogs.initial_data import register_slot, BaseDataSlot
except (ImportError, ModuleNotFoundError):
    raise ImportError("register_slot and BaseDataSlot must be available from django_catalogs.")



DOCUMENT_MANAGER_DOCUMENT_TYPES_DIR = getattr(
    settings, 'DOCUMENT_MANAGER_DOCUMENT_TYPES_DIR',
    Path(__file__).resolve().parent.parent / 'data' / 'document_types'
)

@register_slot(DocumentType, 'document_types', DOCUMENT_MANAGER_DOCUMENT_TYPES_DIR)
class DocumentTypesCatalog(BaseDataSlot):
    pass