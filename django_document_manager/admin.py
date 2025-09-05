from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import DocumentType, Document, DocumentVersion


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'max_file_size_mb', 'requires_validation', 'is_financial', 'is_selectable']
    list_filter = ['requires_validation', 'is_financial', 'is_selectable']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['date_created', 'date_updated']


class DocumentVersionInline(admin.TabularInline):
    model = DocumentVersion
    extra = 0
    readonly_fields = ['version', 'file_size_bytes', 'file_hash', 'mime_type', 'is_current', 'date_created']
    fields = ['version', 'file', 'file_original_name', 'file_size_display', 'is_current', 'document_date']
    
    def file_size_display(self, obj):
        return obj.get_file_size_display() if obj.file_size_bytes else ''
    file_size_display.short_description = 'File Size'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'document_type', 'owner_display', 'validation_status', 
        'access_level', 'is_confidential', 'expiration_date', 'date_created'
    ]
    list_filter = [
        'document_type', 'validation_status', 'access_level', 
        'is_confidential', 'expiration_date', 'date_created'
    ]
    search_fields = ['title', 'description', 'owner_uuid']
    readonly_fields = [
        'owner_uuid', 'owner_model', 'date_created', 'date_updated',
        'ai_extracted_data', 'ai_confidence_score'
    ]
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'document_type')
        }),
        ('Ownership', {
            'fields': ('owner_uuid', 'owner_model'),
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
    
    def owner_display(self, obj):
        owner = obj.get_owner_instance()
        if owner:
            return str(owner)
        return f"UUID: {obj.owner_uuid}"
    owner_display.short_description = 'Owner'


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = [
        'document', 'version', 'file_original_name', 'file_size_display', 
        'mime_type', 'is_current', 'document_date', 'date_created'
    ]
    list_filter = ['is_current', 'mime_type', 'document_date', 'date_created']
    search_fields = ['document__title', 'file_original_name', 'file_hash']
    readonly_fields = [
        'version', 'file_size_bytes', 'file_hash', 'mime_type', 
        'date_created', 'date_updated'
    ]
    
    def file_size_display(self, obj):
        return obj.get_file_size_display()
    file_size_display.short_description = 'File Size'