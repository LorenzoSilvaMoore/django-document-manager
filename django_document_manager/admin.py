from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db import models

from .models import DocumentType, Document, DocumentVersion


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'max_file_size_mb', 'file_extensions_display', 'requires_validation', 'is_financial', 'is_selectable']
    list_filter = ['requires_validation', 'is_financial', 'is_selectable']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['date_created', 'date_updated']
    ordering = ['name']
    list_per_page = 50
    
    def file_extensions_display(self, obj):
        if obj.file_extensions:
            extensions = obj.file_extensions[:3]  # Show first 3 extensions
            display = ', '.join(extensions)
            if len(obj.file_extensions) > 3:
                display += f' (+{len(obj.file_extensions) - 3} more)'
            return display
        return '-'
    file_extensions_display.short_description = 'File Extensions'


class DocumentVersionInline(admin.TabularInline):
    model = DocumentVersion
    extra = 0
    readonly_fields = ['version', 'file_size_bytes', 'file_hash', 'mime_type', 'is_current', 'date_created', 'file_size_display']
    fields = ['version', 'file', 'file_original_name', 'file_size_display', 'mime_type', 'is_current', 'document_date']
    ordering = ['-version']  # Show newest versions first
    
    def file_size_display(self, obj):
        return obj.get_file_size_display() if obj.file_size_bytes else '-'
    file_size_display.short_description = 'File Size'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'document_type', 'owner_display', 'validation_status', 
        'access_level', 'is_confidential', 'current_version_display', 'expiration_status', 'date_created'
    ]
    list_filter = [
        'document_type', 'validation_status', 'access_level', 
        'is_confidential', ('expiration_date', admin.DateFieldListFilter), 
        ('date_created', admin.DateFieldListFilter)
    ]
    search_fields = ['title', 'description', 'owner_uuid']
    readonly_fields = [
        'owner_uuid', 'owner_content_type', 'date_created', 'date_updated',
        'ai_extracted_data', 'ai_confidence_score'
    ]
    date_hierarchy = 'date_created'
    ordering = ['-date_created']
    list_per_page = 25
    actions = ['mark_as_validated', 'mark_as_pending']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'document_type')
        }),
        ('Ownership', {
            'fields': ('owner_uuid', 'owner_content_type'),
            'classes': ('collapse',)
        }),
        ('Validation', {
            'fields': ('validation_status', 'validated_by', 'validation_date', 'validation_notes')
        }),
        ('Access Control', {
            'fields': ('access_level', 'is_confidential', 'expiration_date')
        }),
        ('AI Processing', {
            'fields': ('ai_extracted_data', 'ai_confidence_score'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('date_created', 'date_updated'),
            'classes': ('collapse',)
        })
    )
    inlines = [DocumentVersionInline]
    
    def owner_display(self, obj: 'Document'):
        owner = obj.owner  # Use the new property
        if owner:
            return str(owner)
        return f"UUID: {obj.owner_uuid}"
    owner_display.short_description = 'Owner'
    
    def current_version_display(self, obj):
        current_version = obj.get_current_version()
        if current_version:
            return f"v{current_version.version}"
        return 'No versions'
    current_version_display.short_description = 'Current Version'
    
    def expiration_status(self, obj):
        if not obj.expiration_date:
            return '-'
        if obj.is_expired():
            return format_html('<span style="color: red; font-weight: bold;">Expired</span>')
        else:
            return format_html('<span style="color: green;">Valid</span>')
    expiration_status.short_description = 'Status'
    
    def mark_as_validated(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            validation_status='validated',
            validated_by=request.user,
            validation_date=timezone.now()
        )
        self.message_user(request, f'{updated} documents marked as validated.')
    mark_as_validated.short_description = "Mark selected documents as validated"
    
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(
            validation_status='pending',
            validated_by=None,
            validation_date=None
        )
        self.message_user(request, f'{updated} documents marked as pending.')
    mark_as_pending.short_description = "Mark selected documents as pending"


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = [
        'document_link', 'version', 'file_original_name', 'file_size_display', 
        'mime_type', 'is_current_display', 'document_date', 'date_created'
    ]
    list_filter = [
        'is_current', 'mime_type', 
        ('document_date', admin.DateFieldListFilter), 
        ('date_created', admin.DateFieldListFilter)
    ]
    search_fields = ['document__title', 'file_original_name', 'file_hash']
    readonly_fields = [
        'version', 'file_size_bytes', 'file_hash', 'mime_type', 
        'date_created', 'date_updated'
    ]
    date_hierarchy = 'date_created'
    ordering = ['-date_created']
    list_per_page = 50
    
    def document_link(self, obj):
        if obj.document:
            url = reverse('admin:django_document_manager_document_change', args=[obj.document.pk])
            return format_html('<a href="{}">{}</a>', url, obj.document.title)
        return '-'
    document_link.short_description = 'Document'
    document_link.admin_order_field = 'document__title'
    
    def is_current_display(self, obj):
        if obj.is_current:
            return format_html('<span style="color: green; font-weight: bold;">✓ Current</span>')
        else:
            return format_html('<span style="color: gray;">-</span>')
    is_current_display.short_description = 'Current'
    is_current_display.admin_order_field = 'is_current'
    
    def file_size_display(self, obj):
        return obj.get_file_size_display()
    file_size_display.short_description = 'File Size'
    file_size_display.admin_order_field = 'file_size_bytes'