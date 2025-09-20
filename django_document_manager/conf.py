import logging

from pathlib import Path

from django_crud_audit.conf import _get_django_settings, _get_django_improperly_configured


logger = logging.getLogger(__name__)


class Settings:
    """
    Settings for django_catalogs app
    """

    def __init__(self):
        self._DOCUMENTS_DOCUMENTTYPES_PATH = self._get_document_types_path()
        self.__post_init__()

    def __post_init__(self):
        if not self.DOCUMENTS_DOCUMENTTYPES_PATH.is_file():
            raise _get_django_improperly_configured()(f"DOCUMENTS_DOCUMENTTYPES_PATH file does not exist: {self.DOCUMENTS_DOCUMENTTYPES_PATH}.\n\tHINT: settings.BASE_DIR is used to resolve relative paths, but fallback to cwd: {Path.cwd()}")

    @property
    def DOCUMENTS_DOCUMENTTYPES_PATH(self) -> Path:
        return self._DOCUMENTS_DOCUMENTTYPES_PATH
    
    def _get_document_types_path(self) -> Path:
        file_path = getattr(
            _get_django_settings(), 'DOCUMENTS_DOCUMENTTYPES_PATH', None
        )
        if file_path is None:
            raise _get_django_improperly_configured()("DOCUMENTS_DOCUMENTTYPES_PATH is not set.")
        
        file_path = Path(file_path)
        # Check is is universal path
        if not file_path.is_absolute():
            file_path = getattr(
                _get_django_settings(), 'BASE_DIR', Path.cwd()
            ) / file_path
        return file_path

# Initialize settings instance
documents_settings = Settings()

# Export the settings instance
__all__ = ['documents_settings']