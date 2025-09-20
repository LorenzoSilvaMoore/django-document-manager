from django_catalogs.initial_data.loaded_data import register_slot, BaseDataSlot

from .conf import documents_settings


@register_slot('django_document_manager.documenttype', 'document_types', documents_settings.DOCUMENTS_DOCUMENTTYPES_PATH)
class DocumentTypesCatalog(BaseDataSlot):
    DTYPES = BaseDataSlot.DTYPES | {
        'file_extensions': list,
    }
    NON_EMPTY_KEYS = BaseDataSlot.NON_EMPTY_KEYS + ['file_extensions']
    VERBOSE_NAME = "Document Types Slot"

