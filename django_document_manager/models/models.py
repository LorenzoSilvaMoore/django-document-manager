import os
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
from django.utils.text import get_valid_filename

from django.contrib.contenttypes.models import ContentType

try:
    from django_crud_audit.models import BaseModel, AuditableManager, AuditableQuerySet
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


def _generate_uuid7():
    return uuid6.uuid7()

logger = logging.getLogger(__name__)

class DocumentType(BaseCatalogModel):
    """
    Types of documents that can be uploaded to the system
    """
    DEFAULT_CODE_ID = getattr(settings, 'DOCUMENT_MANAGER_DEFAULT_DOCUMENT_TYPE_CODE', -1)

    code = models.CharField(
        max_length=getattr(settings, 'DOCUMENT_MANAGER_DOCUMENT_TYPE_CODE_MAX_LENGTH', 50),
    )
    
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
    Generate upload path for document files.
    
    Best practice: Returns full path including sanitized filename.
    Organizes files by owner UUID and version for better structure.
    """    
    # Sanitize filename to prevent directory traversal and problematic characters
    clean_filename = get_valid_filename(filename)
    
    # If document doesn't have an ID yet, create a temporary path
    # The file will be moved to proper location after document is saved
    if not instance.document or not instance.document.pk:
        # Use a temporary UUID-based path
        temp_id = str(uuid6.uuid7())
        return f"documents/temp/{temp_id}/{clean_filename}"
    
    # Use owner UUID for the path (better than document ID for privacy/security)
    owner_path = str(instance.document.owner_uuid)
    
    # Version prefix helps identify file versions and prevents overwrites
    # If version not set yet (pre-save), use a timestamp to ensure uniqueness
    if instance.version:
        versioned_filename = f"v{instance.version}_{clean_filename}"
    else:
        # Fallback during initial upload before version is assigned
        import time
        timestamp = int(time.time() * 1000)  # millisecond precision
        versioned_filename = f"tmp{timestamp}_{clean_filename}"

    all_path = f"documents/{owner_path}/{versioned_filename}"

    # Check for length limits (Django/FileSystem)
    max_path_length = 255  # Typical max filename length on many filesystems
    if len(all_path) > max_path_length:
        logger.warning(f"File path length exceeds {max_path_length} characters: {all_path}, truncating filename.")
        # Truncate the filename to fit within the limit
        excess_length = len(all_path) - max_path_length
        truncated_filename = versioned_filename[:-excess_length]
        all_path = f"documents/{owner_path}/{truncated_filename}"

    return all_path


# TODO: hack .save to compute file_size_bytes and file_hash
class DocumentVersion(BaseModel):
    """
    Document versioning for a given document
    """
    # File Information
    file = models.FileField(
        upload_to=document_upload_to,
        help_text=_("The actual document file"),
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

    def clean(self):
        """
        Validate file against DocumentType restrictions.
        This is called by full_clean() and should be called before saving.
        """
        super().clean()
        
        if not self.file:
            return
        
        # Get the document type for validation
        if not self.document or not self.document.document_type:
            return  # Can't validate without document type
        
        document_type = self.document.document_type
        
        # Validate file extension
        if document_type.file_extensions:  # Only validate if list is not empty
            file_extension = os.path.splitext(self.file.name)[1].lower()
            # Remove leading dot if present for comparison
            file_extension = file_extension.lstrip('.')
            
            # Normalize extensions in the allowed list (remove dots, lowercase)
            allowed_extensions = [
                ext.lstrip('.').lower() 
                for ext in document_type.file_extensions
            ]
            
            if file_extension not in allowed_extensions:
                allowed_ext_str = ', '.join([f'.{ext}' for ext in allowed_extensions])
                raise ValidationError({
                    'file': ValidationError(
                        _(f"File extension '.{file_extension}' is not allowed for document type '{document_type.name}'. "
                          f"Allowed extensions: {allowed_ext_str}"),
                        code='invalid_extension'
                    )
                })
        
        # Validate file size
        if hasattr(self.file, 'size'):
            file_size_mb = self.file.size / (1024 * 1024)  # Convert bytes to MB
            max_size_mb = document_type.max_file_size_mb
            
            if file_size_mb > max_size_mb:
                raise ValidationError({
                    'file': ValidationError(
                        _(f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed size "
                          f"for document type '{document_type.name}' ({max_size_mb} MB)."),
                        code='file_too_large'
                    )
                })

    def save(self, *args, **kwargs):
        """
        Override save to compute file metadata and validate.
        """
        # If file was uploaded and we need to compute metadata
        if self.file and not self.file_hash:
            try:
                # Compute file size
                self.file_size_bytes = self.file.size
                
                # Compute SHA-256 hash
                self.file_hash = self.compute_file_hash()

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

        # Run validation (this calls clean())
        # Skip validation if explicitly requested via kwargs
        # This happens AFTER metadata computation and version assignment
        if not kwargs.pop('skip_validation', False):
            self.full_clean(exclude=['file_size_bytes', 'file_hash', 'mime_type', 'version'])

        # # If this is being set as current, unset other current versions
        # if self.is_current and self.document.id:
        #     self.document.versions.exclude(pk=self.pk).update(is_current=False)

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
    
    def compute_file_hash(self):
        """
        Recompute the file hash (useful if file was modified externally)
        """
        if not self.file:
            raise ValueError("No file associated with this version")
        
        hasher = hashlib.sha256()
        for chunk in self.file.chunks():
            hasher.update(chunk)
        
        file_hash = hasher.hexdigest()
        return file_hash

    def __str__(self):
        return f"{self.document.title} v{self.version}"

    def __repr__(self):
        return f"DocumentVersion(document={self.document.pk}, version={self.version}, current={self.is_current})"

class DocumentGroup(models.Model):
    """
    Model to group documents by related owner entities.
    This allows associating multiple document owners under a common group UUID.
    """
    group_uuid = models.UUIDField(
        primary_key=True,
        default=_generate_uuid7,
        editable=False,
        help_text=_("Unique identifier for the document group")
    )
    name = models.CharField(
        max_length=200,
        help_text=_("Name of the document group")
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text=_("Description of the document group")
    )
    metadata = models.JSONField(
        null=True,
        blank=True,
        help_text=_("Additional metadata for the document group")
    )

    class Meta:
        db_table = 'dm_document_group'
        verbose_name = _('document group')
        verbose_name_plural = _('document groups')

    def __str__(self):
        return f"{self.name} ({self.group_uuid})"


class DocumentQuerySet(AuditableQuerySet):
    """
    Custom queryset for Document model
    """
    def in_groups(self, groups):
        """
        Filter documents that belong to any of the specified groups.
        
        Args:
            groups: Can be one of the following:
                   - DocumentGroup QuerySet
                   - List/tuple containing:
                     * DocumentGroup instances
                     * UUID objects
                     * UUID strings
                     * Mix of the above types
                   - Single DocumentGroup instance
                   - Related manager (e.g., owner.document_groups)
                   
        Returns:
            QuerySet: Documents that belong to any of the specified groups
            
        Raises:
            ValueError: If groups parameter or its contents are invalid
            
        Examples:
            # Using a DocumentGroup queryset
            Document.objects.in_groups(DocumentGroup.objects.filter(name__startswith='Sales'))
            
            # Using DocumentGroup instances
            group = DocumentGroup.objects.first()
            Document.objects.in_groups([group])
            
            # Using related manager
            owner = MyModel.objects.first()
            Document.objects.in_groups(owner.document_groups.all())
            
            # Using UUID objects
            Document.objects.in_groups([uuid.UUID('...'), uuid.UUID('...')])
            
            # Using UUID strings
            Document.objects.in_groups(['550e8400-e29b-41d4-a716-446655440000', ...])
            
            # Mixed types
            Document.objects.in_groups([group_instance, uuid_obj, 'uuid-string'])
            
            # Chain with other filters
            Document.objects.in_groups([group]).filter(document_type__code='invoice')
        """
        import uuid as uuid_module
        from django.db.models import QuerySet
        from django.db.models.manager import BaseManager
        
        # Handle QuerySet or Manager (like related manager owner.document_groups)
        if isinstance(groups, (QuerySet, BaseManager)):
            # Extract group_uuid values from the queryset
            group_uuids = groups.values_list('group_uuid', flat=True)
            if not group_uuids:
                return self.none()
            return self.filter(groups__group_uuid__in=group_uuids).distinct()
        
        # Handle single DocumentGroup instance
        if isinstance(groups, DocumentGroup):
            return self.filter(groups__group_uuid=groups.group_uuid).distinct()
        
        # Validate input is a list or tuple
        if not isinstance(groups, (list, tuple)):
            raise ValueError(
                "groups parameter must be a DocumentGroup instance, QuerySet, "
                f"or list/tuple of groups/UUIDs. Got {type(groups).__name__} instead."
            )
        
        # Empty list should return empty queryset
        if not groups:
            return self.none()
        
        # Validate and normalize to UUIDs
        validated_uuids = []
        for idx, group in enumerate(groups):
            if isinstance(group, DocumentGroup):
                # DocumentGroup instance
                validated_uuids.append(group.group_uuid)
            elif isinstance(group, uuid_module.UUID):
                # Already a UUID object, use it directly
                validated_uuids.append(group)
            elif isinstance(group, str):
                # String - attempt to parse as UUID
                try:
                    validated_uuids.append(uuid_module.UUID(group))
                except (ValueError, AttributeError) as e:
                    raise ValueError(
                        f"Invalid UUID string at index {idx}: '{group}'. "
                        f"Must be a valid UUID format. Error: {e}"
                    )
            else:
                # Invalid type
                raise ValueError(
                    f"Invalid type at index {idx}: {type(group).__name__}. "
                    "Each group identifier must be a DocumentGroup instance, "
                    "UUID object, or valid UUID string."
                )
        
        # Filter documents by groups
        return self.filter(groups__group_uuid__in=validated_uuids).distinct()


class DocumentManager(AuditableManager.from_queryset(DocumentQuerySet)):
    """
    Custom manager for Document model that includes DocumentQuerySet methods.
    This combines the auditable functionality with custom queryset methods.
    """
    def get_queryset(self):
        """Override to use DocumentQuerySet and filter deleted items"""
        return DocumentQuerySet(self.model, using=self._db).filter(date_deleted__isnull=True)

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
    owner_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text=_("Content type of the document owner")
    )
    owner_uuid = models.UUIDField(
        help_text=_("UUID of the document owner instance")
    )
    groups = models.ManyToManyField(
        DocumentGroup,
        blank=True,
        related_name="documents",
        help_text=_("Groups this document belongs to")
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
    
    # Custom manager
    objects = DocumentManager()

    @property
    def owner(self):
        """
        Get the document owner instance based on content type and object ID.
        Uses caching to avoid repeated database hits.
        """
        cache_attr = '_owner_cache'
        if hasattr(self, cache_attr):
            return getattr(self, cache_attr)
        
        try:
            model_class = self.owner_content_type.model_class()
            if model_class is None:
                setattr(self, cache_attr, None)
                return None
                
            owner_instance = model_class.objects.get(document_owner_uuid=self.owner_uuid)
            setattr(self, cache_attr, owner_instance)
            return owner_instance
        except (AttributeError, Exception) as e:
            # Handle any model DoesNotExist or other exceptions
            try:
                if hasattr(e, '__class__') and 'DoesNotExist' in e.__class__.__name__:
                    logger.warning(f"Owner with UUID {self.owner_uuid} not found for content type {self.owner_content_type}")
                else:
                    logger.warning(f"Error resolving owner: {e}")
            except:
                pass
            setattr(self, cache_attr, None)
            return None
        
    def set_owner(self, owner_instance: 'BaseDocumentOwnerModel'):
        """Set the owner using both ContentType and UUID"""
        self.owner_content_type = ContentType.objects.get_for_model(owner_instance)
        self.owner_uuid = owner_instance.document_owner_uuid

        # Clear cache when owner changes
        if hasattr(self, '_owner_cache'):
            delattr(self, '_owner_cache')

    def clean(self):
        """
        Custom validation for document data
        """
        super().clean()
        
        # Validate that we have a valid owner
        if not self.owner_uuid:
            raise ValidationError(_("Document must have an owner"))

        if not self.owner_content_type:
            raise ValidationError(_("Document must specify owner content type"))

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
            models.Index(fields=['owner_content_type', 'owner_uuid'], name='idx_owner_ct_uuid'),

            models.Index(fields=['document_type'], name='idx_document_type'),
            models.Index(fields=['validation_status'], name='idx_document_validation'),

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

    def is_expired(self) -> bool:
        """
        Check if document is expired
        """
        if not self.expiration_date:
            return False
        return self.expiration_date < timezone.now().date()

    def set_current_version(self, version: 'DocumentVersion') -> None:
        """
        Set the current version of the document.
        """
        if version.document_id != self.id:
            raise ValidationError("Version does not belong to this document")
        
        current = self.get_current_version()
        with transaction.atomic():
            if current:
                current.is_current = False
                current.save(update_fields=['is_current'])

            version.is_current = True
            version.save(update_fields=['is_current'])

    def save_new_version(self, file, set_current: bool = True, strict: bool = True, **kwargs) -> 'DocumentVersion':
        """
        Save a new version of the document with atomic version increment.
        If 'strict' is True, will raise ValidationError if there is a hash collision,
        otherwise will reuse existing version with same hash.
        
        Raises:
            ValidationError: If file extension or size doesn't meet DocumentType requirements
        """
        with transaction.atomic():
            # Create new version
            new_version = DocumentVersion(
                document=self,
                file=file,
                is_current=False,  # Will set current later if needed
            )
            
            # Validate only the file-related aspects (extension and size)
            # Don't validate other fields that aren't set yet (hash, size_bytes, mime_type, version)
            try:
                new_version.clean()  # This only validates file extension and size
            except ValidationError as e:
                # Re-raise with more context
                logger.warning(f"File validation failed for new version of document {self.pk}: {e}")
                raise
            
            # Compute file hash to check for duplicates
            file_hash = new_version.compute_file_hash()
            existing_version = DocumentVersion.objects.filter(
                document=self,
                file_hash=file_hash,
            ).first()

            if existing_version:
                if strict:
                    raise ValidationError("A version with the same file already exists.")
                logger.info(f"Reusing existing version {existing_version.version} for document {self.pk} due to identical file hash.")
                new_version = existing_version
                if set_current:
                    self.set_current_version(existing_version)
                return existing_version

            # Save the new version (will auto-compute metadata and version number)
            # Validation will run during save but will exclude auto-computed fields
            new_version.save()

            if set_current:
                self.set_current_version(new_version)

            return new_version

    @classmethod
    def create_with_file(cls, owner: 'BaseDocumentOwnerModel', file, document_type: str, title: str, description: str = None, **kwargs) -> 'Document':
        """
        Create a new document with its first version
        """
        # Validate ownership
        if not isinstance(owner, BaseDocumentOwnerModel):
            raise ValidationError("Owner must be an instance of BaseDocumentOwnerModel or its subclass")
        
        # Get document type
        if isinstance(document_type, str):
            document_type = DocumentType.get_by_code(document_type)
            if not document_type:
                raise ValidationError(f"Invalid document type: {document_type}")
        
        # Create document
        document = cls(
            owner_content_type=ContentType.objects.get_for_model(owner),
            owner_uuid=owner.document_owner_uuid,
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
        
    def get_owner_display(self):
        """
        Return the display name of the document owner
        """
        owner_instance = self.owner
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
        
        # UUID7 encodes the timestamp, so we can construct a cutoff UUID
        # All documents created after cutoff_time will have UUIDs >= to this cutoff
        # Generate a UUID7 for comparison (we'll compare timestamps instead of UUIDs for simplicity)
        return cls.objects.filter(
            owner_uuid=owner_uuid,
            date_created__gte=cutoff_time  # Use date_created timestamp field
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

class DocumentOwnerManager(AuditableManager):
    """
    Manager for Document Owner models to facilitate document queries
    and guarantee UUID generation for all operations
    """
    def get_queryset(self):
        """Return custom queryset that handles UUID generation"""
        return DocumentOwnerQuerySet(self.model, using=self._db)
    
    def create(self, **kwargs):
        """
        Override create to ensure document_owner_uuid is set
        """
        if 'document_owner_uuid' not in kwargs or kwargs['document_owner_uuid'] is None:
            kwargs['document_owner_uuid'] = _generate_uuid7()
        return super().create(**kwargs)
    
    def get_or_create(self, defaults=None, **kwargs):
        """
        Override get_or_create to ensure document_owner_uuid is set on creation
        """
        if defaults is None:
            defaults = {}
        if 'document_owner_uuid' not in defaults and 'document_owner_uuid' not in kwargs:
            defaults['document_owner_uuid'] = _generate_uuid7()
        return super().get_or_create(defaults=defaults, **kwargs)
    
    def update_or_create(self, defaults=None, **kwargs):
        """
        Override update_or_create to ensure document_owner_uuid is set on creation
        Note: UUIDs are never updated for existing records, only set for new ones
        """
        if defaults is None:
            defaults = {}
        # Ensure UUID is generated for new instances
        if 'document_owner_uuid' not in defaults and 'document_owner_uuid' not in kwargs:
            defaults['document_owner_uuid'] = _generate_uuid7()
        # Remove document_owner_uuid from defaults if it's None (prevent overwriting existing UUIDs)
        if 'document_owner_uuid' in defaults and defaults['document_owner_uuid'] is None:
            del defaults['document_owner_uuid']
        return super().update_or_create(defaults=defaults, **kwargs)
    
    def bulk_create(self, objs, **kwargs):
        """
        Override bulk_create to ensure document_owner_uuid is set for all objects
        """
        for obj in objs:
            if not obj.document_owner_uuid:
                obj.document_owner_uuid = _generate_uuid7()
        return super().bulk_create(objs, **kwargs)
    
    def bulk_update(self, objs, fields, **kwargs):
        """
        Override bulk_update to ensure document_owner_uuid is never modified
        """
        if 'document_owner_uuid' in fields:
            fields = [f for f in fields if f != 'document_owner_uuid']
        return super().bulk_update(objs, fields, **kwargs)
    
class DocumentOwnerQuerySet(AuditableQuerySet):
    """
    QuerySet for Document Owner models to facilitate document queries
    and guarantee UUID integrity
    """
    def with_documents(self):
        """
        Filter owners that have at least one document
        """
        from .models import Document
        
        owner_uuids = Document.objects.values_list('owner_uuid', flat=True).distinct()
        return self.filter(
            document_owner_uuid__in=owner_uuids,
            document_owner_uuid__isnull=False
        )
    
    def update(self, **kwargs):
        """
        Override update to prevent modifying document_owner_uuid
        and ensure UUIDs are generated for records without them
        """
        # Never allow updating document_owner_uuid via queryset.update()
        if 'document_owner_uuid' in kwargs:
            del kwargs['document_owner_uuid']
            logger.warning(
                "Attempted to update document_owner_uuid via queryset.update(). "
                "UUIDs cannot be modified after creation."
            )
        
        return super().update(**kwargs)
    
    def update_or_create(self, defaults=None, **kwargs):
        """
        Override update_or_create to ensure document_owner_uuid is set on creation
        """
        if defaults is None:
            defaults = {}
        # Ensure UUID is generated for new instances
        if 'document_owner_uuid' not in defaults and 'document_owner_uuid' not in kwargs:
            defaults['document_owner_uuid'] = _generate_uuid7()
        # Remove document_owner_uuid from defaults if it's None
        if 'document_owner_uuid' in defaults and defaults['document_owner_uuid'] is None:
            del defaults['document_owner_uuid']
        return super().update_or_create(defaults=defaults, **kwargs)
    
    def get_or_create(self, defaults=None, **kwargs):
        """
        Override get_or_create to ensure document_owner_uuid is set on creation
        """
        if defaults is None:
            defaults = {}
        if 'document_owner_uuid' not in defaults and 'document_owner_uuid' not in kwargs:
            defaults['document_owner_uuid'] = _generate_uuid7()
        return super().get_or_create(defaults=defaults, **kwargs)
    
    def bulk_create(self, objs, **kwargs):
        """
        Override bulk_create to ensure document_owner_uuid is set
        """
        for obj in objs:
            if not obj.document_owner_uuid:
                obj.document_owner_uuid = _generate_uuid7()
        return super().bulk_create(objs, **kwargs)

class BaseDocumentOwnerModel(BaseModel):
    """
    Abstract base model for entities that can own documents.
    
    This model provides a UUID field for document ownership without creating
    circular dependencies with the main Document model.
    
    Migration-Safe Design:
    - No callable defaults to avoid Django migration issues
    - null=True allows existing records to work seamlessly
    - unique=True ensures data integrity
    - UUIDs are generated in save() method for new instances
    - Custom manager/queryset ensure UUIDs for bulk operations
    - Use populate_document_owner_uuids management command for existing data
    """
    document_owner_uuid = models.UUIDField(
        null=True,  # Allows existing records to work seamlessly
        blank=True,  # Allows forms to work properly
        editable=False,
        db_index=True, 
        help_text=_("Unique identifier for the document owner entity")
    )

    document_groups = models.ManyToManyField(
        DocumentGroup,
        blank=True,
        related_name="%(app_label)s_%(class)s_owners",
        help_text=_("Document groups associated with this owner")
    )
    
    # Use custom manager to guarantee UUID generation
    objects = DocumentOwnerManager()

    class Meta:
        abstract = True

        constraints = [
            models.UniqueConstraint(
                fields=['document_owner_uuid'],
                name='u_doc_%(app_label)s_%(class)s_uuid',
                condition=models.Q(document_owner_uuid__isnull=False)
            )
        ]

    def __str__(self):
        uuid_display = str(self.document_owner_uuid) if self.document_owner_uuid else "No UUID"
        return f"{self._meta.verbose_name} ({uuid_display})"
    
    def save(self, *args, **kwargs):
        """
        Generate document_owner_uuid if it doesn't exist.
        This handles both new instances and existing instances that don't have UUIDs yet.
        """
        if not self.document_owner_uuid:
            # Generate UUID7 for new instances or existing instances without UUIDs
            self.document_owner_uuid = _generate_uuid7()
            
            # For extra safety, ensure uniqueness in case of race conditions
            max_attempts = 10
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    # Check if this UUID already exists for this model
                    if self.__class__.objects.filter(
                        document_owner_uuid=self.document_owner_uuid
                    ).exclude(pk=self.pk).exists():
                        # Generate a new UUID and try again
                        self.document_owner_uuid = _generate_uuid7()
                        attempt += 1
                        continue
                    else:
                        # UUID is unique, break out of loop
                        break
                except Exception as e:
                    logger.warning(f"Error checking UUID uniqueness: {e}")
                    # Generate new UUID and try again
                    self.document_owner_uuid = _generate_uuid7()
                    attempt += 1
            
            if attempt >= max_attempts:
                logger.error(f"Could not generate unique document_owner_uuid after {max_attempts} attempts")
                raise ValidationError(
                    _("Unable to generate unique document owner UUID. Please try again.")
                )
        
        super().save(*args, **kwargs)

    def get_display_name(self):
        """
        Return a display name for the owner entity.
        Override this method in your concrete models.
        """
        return str(self)

    def get_or_create_document_owner_uuid(self):
        """
        Ensure this instance has a document_owner_uuid.
        This method is useful for existing instances that might not have UUIDs yet.
        
        Returns:
            UUID: The document_owner_uuid for this instance
        """
        if not self.document_owner_uuid:
            self.document_owner_uuid = _generate_uuid7()
            # Save only the UUID field to avoid triggering other save logic
            self.save(update_fields=['document_owner_uuid'])
        return self.document_owner_uuid

    def get_documents(self):
        """
        Return queryset of documents owned by this entity.
        
        Note: This method imports Document at runtime to avoid circular imports.
        For instances without UUIDs, returns empty queryset.
        """
        if not self.document_owner_uuid:
            # Return empty queryset for instances without UUIDs
            from .models import Document
            return Document.objects.none()
            
        # Import here to avoid circular dependency issues
        from .models import Document
        return Document.objects.filter(
            owner_uuid=self.document_owner_uuid
        )
    
    def get_documents_by_type(self, document_type_code):
        """
        Get documents of a specific type owned by this entity.
        
        Args:
            document_type_code (str): Code of the document type
            
        Returns:
            QuerySet: Documents of the specified type
        """
        if not self.document_owner_uuid:
            # Return empty queryset for instances without UUIDs
            from .models import Document
            return Document.objects.none()
            
        # Import here to avoid circular dependency issues  
        from .models import Document
        return self.get_documents().filter(
            document_type__code=document_type_code
        )
    
    def get_recent_documents(self, limit=10):
        """
        Get most recent documents owned by this entity.
        Uses UUID7 time ordering for efficient queries.
        
        Args:
            limit (int): Maximum number of documents to return
            
        Returns:
            QuerySet: Most recent documents
        """
        if not self.document_owner_uuid:
            # Return empty queryset for instances without UUIDs
            from .models import Document
            return Document.objects.none()
            
        return self.get_documents().order_by('-id')[:limit]
    
    @classmethod
    def get_owners_with_documents(cls):
        """
        Get all owners that have at least one document.
        Only includes owners with valid UUIDs.
        
        Returns:
            QuerySet: Owner instances that have documents
        """
        # Import here to avoid circular dependency issues
        from .models import Document
        
        owner_uuids = Document.objects.values_list('owner_uuid', flat=True).distinct()
        # Filter out None UUIDs and ensure our instances have UUIDs too
        return cls.objects.filter(
            document_owner_uuid__in=owner_uuids,
            document_owner_uuid__isnull=False
        )