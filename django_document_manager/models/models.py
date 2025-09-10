import logging
import hashlib
import mimetypes

from typing import Optional

from django.db import models, transaction
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

try:
    from django_crud_audit.models import BaseModel
except (ImportError, ModuleNotFoundError):
    raise ImportError("BaseModel must be available from django_crud_audit.")

try:
    from django_catalogs.models import BaseCatalogModel
except (ImportError, ModuleNotFoundError):
    raise ImportError("BaseCatalogModel must be available from django_catalogs.")

try:
    import uuid6
except (ImportError, ModuleNotFoundError):
    raise ImportError("uuid7 package must be available for uuid7 support.")




logger = logging.getLogger(__name__)

class DocumentType(BaseCatalogModel):
    """
    Types of documents that can be uploaded to the system
    """
    DEFAULT_CODE_ID = getattr(settings, 'DOCUMENT_MANAGER_DEFAULT_DOCUMENT_TYPE_CODE', 'generic')
    
    # Document-specific fields
    file_extensions = models.JSONField(
        default=list,
        help_text=_("Allowed file extensions for this document type")
    )
    max_file_size_mb = models.IntegerField(
        default=10,
        help_text=_("Maximum file size in MB")
    )
    requires_validation = models.BooleanField(
        default=False,
        help_text=_("Whether this document type requires manual validation")
    )
    is_financial = models.BooleanField(
        default=False,
        help_text=_("Whether this is a financial document requiring special handling")
    )
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def __repr__(self):
        return f"DocumentType(name={self.name}, code={self.code})"
    
    class Meta:
        db_table = 'dm_document_type'
        verbose_name = _('document type')
        verbose_name_plural = _('document types')



# Document upload path function
def document_upload_to(instance, filename):
    """
    Generate upload path for document files
    """
    # If document doesn't have an ID yet, create a temporary path
    # The file will be moved to proper location after document is saved
    if not instance.document or not instance.document.pk:
        # Use a temporary UUID-based path
        temp_id = str(uuid6.uuid7())
        return f"documents/temp/{temp_id}/{filename}"
    
    # Use actual document ID for the path
    return f"documents/{instance.document.owner_uuid}/{instance.version}_{filename}"


# TODO: hack .save to compute file_size_bytes and file_hash
class DocumentVersion(BaseModel):
    """
    Document versioning for a given document
    """
    # File Information
    file = models.FileField(
        upload_to=document_upload_to,
        help_text=_("The actual document file")
    )
    file_size_bytes = models.BigIntegerField(
        help_text=_("Size of the file in bytes")
    )
    file_hash = models.CharField(
        max_length=64,
        help_text=_("SHA-256 hash of file contents for integrity verification")
    )
    mime_type = models.CharField(
        max_length=100,
        help_text=_("MIME type of the file")
    )
    file_original_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Original name of the uploaded file")
    )

    # Version tracking
    document = models.ForeignKey(
        'Document',
        on_delete=models.CASCADE,
        related_name='versions',
        help_text=_("Document this version belongs to")
    )
    version = models.PositiveIntegerField(help_text=_("Version number of the document"))
    is_current = models.BooleanField(default=True, help_text=_("Whether this is the current version"))
    replaced_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replaces'
    )

    # Document Date
    document_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Date the document was created or is effective")
    )

    class Meta:
        db_table = 'dm_document_version'
        verbose_name = _('document version')
        verbose_name_plural = _('document versions')
        ordering = ['document', '-version']

        indexes = [
            models.Index(fields=['document', 'version'], name='document_version_idx'),
            models.Index(fields=['file_hash'], name='file_hash_idx'),
            models.Index(fields=['document_date'], name='document_date_idx'),
            models.Index(fields=['document', 'is_current'], name='document_is_current_idx')
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['document', 'version'],
                name='unique_document_version',
                condition=models.Q(date_deleted__isnull=True)
            ),
            models.UniqueConstraint(
                fields=['document', 'is_current'],
                name='unique_document_current',
                condition=models.Q(date_deleted__isnull=True, is_current=True)
            ),
            models.UniqueConstraint(
                fields=['document', 'file_hash'],
                name='unique_document_file_hash',
                condition=models.Q(date_deleted__isnull=True)
            )
        ]

    def get_file_size_display(self):
        """
        Return human-readable file size
        """
        if self.file_size_bytes < 1024:
            return f"{self.file_size_bytes} B"
        elif self.file_size_bytes < 1024 * 1024:
            return f"{self.file_size_bytes / 1024:.1f} KB"
        elif self.file_size_bytes < 1024 * 1024 * 1024:
            return f"{self.file_size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def save(self, *args, **kwargs):
        """
        Override save to compute file metadata
        """
        import os
        
        # If file was uploaded and we need to compute metadata
        if self.file and not self.file_hash:
            try:
                # Compute file size
                self.file_size_bytes = self.file.size
                
                # Compute SHA-256 hash
                hasher = hashlib.sha256()
                for chunk in self.file.chunks():
                    hasher.update(chunk)
                self.file_hash = hasher.hexdigest()
                
                # Detect MIME type
                mime_type, _ = mimetypes.guess_type(self.file.name)
                self.mime_type = mime_type or 'application/octet-stream'
            except (IOError, OSError) as e:
                logger.error(f"Error processing file {self.file.name}: {e}")
                raise ValidationError(f"Error processing file: {e}")
        
        # Auto-increment version number if not set (with atomic transaction)
        if not self.version and self.document_id:
            with transaction.atomic():
                # Lock the document row to prevent race conditions
                Document.objects.select_for_update().get(id=self.document_id)
                
                # Use a more robust version calculation excluding this instance if it's being updated
                versions_query = self.document.versions.filter(date_deleted__isnull=True)
                if self.pk:  # If this instance already exists, exclude it from the calculation
                    versions_query = versions_query.exclude(pk=self.pk)
                
                max_version = versions_query.aggregate(
                    max_version=models.Max('version')
                )['max_version'] or 0
                self.version = max_version + 1

        # If this is being set as current, unset other current versions
        if self.is_current and self.document.id:
            self.document.versions.exclude(pk=self.pk).update(is_current=False)

        if not self.file_original_name and self.file:
            self.file_original_name = self.file.name

        super().save(*args, **kwargs)

    def get_download_url(self):
        """
        Get the download URL for this document version
        """
        return reverse('document_manager:download_version', kwargs={
            'document_id': self.document.pk,
            'version': self.version
        })

    def __str__(self):
        return f"{self.document.title} v{self.version}"

    def __repr__(self):
        return f"DocumentVersion(document={self.document.pk}, version={self.version}, current={self.is_current})"



class Document(BaseModel):
    """
    Documents uploaded to the system with metadata and validation
    """
    # Document Classification
    document_type = models.ForeignKey(
        'DocumentType',
        on_delete=models.PROTECT,
        help_text=_("Type of document")
    )

    # Ownership and Relationships
    owner_uuid = models.UUIDField(
        editable=False,
        help_text=_("Unique identifier for the document owner")
    )
    owner_model = models.CharField(
        max_length=255,
        help_text=_("Model name of the document owner (e.g., 'Company', 'Individual', 'User')")
    )
    
    # Document Metadata
    title = models.CharField(
        max_length=200,
        help_text=_("Document title or description")
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text=_("Detailed description of document contents")
    )
    
    # Date Information
    expiration_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Date the document expires (if applicable)")
    )
    
    # Validation and Processing Status Choices
    VALIDATION_STATUS_CHOICES = [
        ('pending', _('Pending Review')),
        ('validated', _('Validated')),
        ('rejected', _('Rejected')),
        ('requires_update', _('Requires Update')),
    ]
    
    ACCESS_LEVEL_CHOICES = [
        ('public', _('Public')),
        ('internal', _('Internal Team')),
        ('restricted', _('Restricted Access')),
        ('confidential', _('Confidential')),
    ]
    
    validation_status = models.CharField(
        max_length=20,
        choices=VALIDATION_STATUS_CHOICES,
        default='pending',
        help_text=_("Current validation status")
    )
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validated_documents',
        help_text=_("User who validated this document")
    )
    validation_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When the document was validated")
    )
    validation_notes = models.TextField(
        null=True,
        blank=True,
        help_text=_("Notes from validation process")
    )
    validation_errors = models.JSONField(default=list)
    
    # AI Processing
    ai_extracted_data = models.JSONField(
        default=dict,
        help_text=_("Data extracted from document by AI processing")
    )
    ai_confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("AI confidence score for extracted data (0-100)")
    )
    
    # Access Control
    is_confidential = models.BooleanField(
        default=False,
        help_text=_("Whether this document contains confidential information")
    )
    access_level = models.CharField(
        max_length=20,
        choices=ACCESS_LEVEL_CHOICES,
        default='internal',
        help_text=_("Who can access this document")
    )
    
    def clean(self):
        """
        Custom validation for document data
        """
        super().clean()
        
        # Validate that we have a valid owner
        if not self.owner_uuid:
            raise ValidationError(_("Document must have an owner"))
        
        if not self.owner_model:
            raise ValidationError(_("Document must specify owner model"))

        # Validate AI confidence score range
        if self.ai_confidence_score is not None and (
            self.ai_confidence_score < 0 or self.ai_confidence_score > 100
        ):
            raise ValidationError(
                _("AI confidence score must be between 0 and 100")
            )

    def __str__(self):
        return f"{self.title} ({self.document_type}, Owner: {self.get_owner_display()})"
    
    def __repr__(self):
        return f"Document(title={self.title}, type={self.document_type.code}, owner={self.owner_uuid})"

    class Meta:
        db_table = 'dm_document'
        verbose_name = _('document')
        verbose_name_plural = _('documents')
        indexes = [
            # uuid7-optimized indexes - time ordering is built into uuid7
            models.Index(fields=['owner_uuid'], name='idx_document_owner_time'),
            models.Index(fields=['document_type'], name='idx_document_type'),
            models.Index(fields=['validation_status'], name='idx_document_validation'),
            models.Index(fields=['access_level'], name='idx_document_access'),
            models.Index(fields=['is_confidential'], name='idx_document_confidential'),
            models.Index(fields=['expiration_date'], name='idx_document_expiration'),
            # Composite index for owner queries by type
            models.Index(fields=['owner_uuid', 'document_type'], name='idx_owner_type'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['owner_uuid', 'title'],
                name='unique_owner_document_title',
                condition=models.Q(date_deleted__isnull=True)
            )
        ]

    def is_expired(self):
        """
        Check if document is expired
        """
        if not self.expiration_date:
            return False
        return self.expiration_date < timezone.now().date()

    def set_current_version(self, version: 'DocumentVersion'):
        """
        Set the current version of the document.
        """
        if version.document_id != self.id:
            raise ValidationError("Version does not belong to this document")
        
        current = self.current_version
        if current:
            current.is_current = False
            current.save()

        version.is_current = True
        version.save()

    def save_new_version(self, file, set_current: bool = True, **kwargs):
        """
        Save a new version of the document with atomic version increment.
        """
        with transaction.atomic():
            # Create new version
            new_version = DocumentVersion(
                document=self,
                file=file,
                is_current=set_current,
                **kwargs
            )
            
            # Save the version (will auto-compute metadata and version number)
            new_version.save()
            
            return new_version

    @classmethod
    def create_with_file(cls, owner: 'BaseDocumentOwnerModel', file, document_type, title, description=None, **kwargs):
        """
        Create a new document with its first version
        """
        # Validate ownership
        if not isinstance(owner, BaseDocumentOwnerModel):
            raise ValidationError("Owner must be an instance of BaseDocumentOwnerModel")
        
        # Get document type
        if isinstance(document_type, str):
            document_type = DocumentType.get_by_code(document_type)
            if not document_type:
                raise ValidationError(f"Invalid document type: {document_type}")
        
        # Create document
        document = cls(
            owner_uuid=owner.document_owner_uuid,
            owner_model=f"{owner._meta.app_label}.{owner._meta.model_name}",
            document_type=document_type,
            title=title,
            description=description,
            **kwargs
        )
        document.save()
        
        # Create first version
        version = document.save_new_version(file, set_current=True)
        logger.info(f"Created document {document} with initial version {version}")
        
        return document
    
    def get_owner_instance(self):
        """
        Return the actual owner model instance
        """
        if not self.owner_model or not self.owner_uuid:
            return None
        
        try:
            # Parse app_label.ModelName format
            if '.' in self.owner_model:
                app_label, model_name = self.owner_model.split('.', 1)
                model_class = apps.get_model(app_label, model_name)
            else:
                # Fallback: assume it's just the model name
                model_class = apps.get_model(self.owner_model)
            
            return model_class.objects.get(document_owner_uuid=self.owner_uuid)
        except (LookupError, model_class.DoesNotExist, ValueError):
            logger.warning(f"Owner model {self.owner_model} with UUID {self.owner_uuid} not found.")
            return None
        
    def get_owner_display(self):
        """
        Return the display name of the document owner
        """
        owner_instance = self.get_owner_instance()
        if owner_instance:
            # Try common display methods
            if hasattr(owner_instance, 'get_display_name'):
                return owner_instance.get_display_name()
            elif hasattr(owner_instance, '__str__'):
                return str(owner_instance)
        return _("No Owner Found or No Display Method")

    def get_latest_version_number(self) -> int:
        """
        Get the latest version number. If no versions exist, return 0.
        """
        latest = self.versions.aggregate(max_version=models.Max('version'))['max_version']
        return latest or 0
    
    def get_version(self, n: int) -> Optional['DocumentVersion']:
        """
        Return the specified version of the document. If it doesn't exist, return None.
        """
        return self.versions.filter(version=n).first()
    
    def get_current_version(self) -> Optional['DocumentVersion']:
        """
        Return the current version of the document. If it doesn't exist, return None.
        """
        return self.versions.filter(is_current=True).first()

    def get_num_versions(self) -> int:
        """
        Return the number of versions of the document.
        """
        return self.versions.count()

    def get_latest_version(self) -> Optional['DocumentVersion']:
        """
        Return the latest version of the document. If it doesn't exist, return None.
        """
        return self.get_version(self.get_latest_version_number())

    @classmethod
    def get_documents_since(cls, owner_uuid, days_ago: int):
        """
        Get documents for an owner created since N days ago.
        Leverages uuid7's time encoding for efficient queries.
        """
        from datetime import datetime, timedelta
        cutoff_time = datetime.now() - timedelta(days=days_ago)
        cutoff_uuid = uuid6.uuid7(cutoff_time)
        
        return cls.objects.filter(
            owner_uuid=owner_uuid,
            id__gte=cutoff_uuid  # Uses uuid7 time ordering
        )

    @classmethod 
    def get_recent_documents(cls, owner_uuid, limit: int = 10):
        """
        Get most recent documents for an owner.
        Since uuid7 is time-ordered, we can order by id (primary key).
        """
        return cls.objects.filter(
            owner_uuid=owner_uuid
        ).order_by('-id')[:limit]  # uuid7 ordering = time ordering



class BaseDocumentOwnerModel(BaseModel):
    """
    Abstract base model for entities that can own documents
    """
    document_owner_uuid = models.UUIDField(
        default=uuid6.uuid7,
        editable=False,
        unique=True,
        help_text=_("Unique identifier for the document owner entity")
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self._meta.verbose_name} ({self.document_owner_uuid})"

    def get_display_name(self):
        """
        Return a display name for the owner entity
        """
        return str(self)

    def get_documents(self):
        """
        Return queryset of documents owned by this entity
        """
        return Document.objects.filter(
            owner_uuid=self.document_owner_uuid
        )