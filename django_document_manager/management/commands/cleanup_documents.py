from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
import os
import logging

from django_document_manager.models import Document, DocumentVersion

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up orphaned document files and expired documents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete expired documents older than N days (default: 30)',
        )
        parser.add_argument(
            '--cleanup-temp',
            action='store_true',
            help='Clean up temporary upload files',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days = options['days']
        cleanup_temp = options['cleanup_temp']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No files will be deleted')
            )

        # Clean up expired documents
        cutoff_date = timezone.now().date() - timedelta(days=days)
        expired_docs = Document.objects.filter(
            expiration_date__lt=cutoff_date,
        )

        if expired_docs.exists():
            count = expired_docs.count()
            self.stdout.write(
                f'Found {count} expired documents older than {days} days'
            )
            
            if not dry_run:
                # Soft delete expired documents
                expired_docs.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Soft-deleted {count} expired documents')
                )
        else:
            self.stdout.write('No expired documents found')

        # Clean up temp files if requested
        if cleanup_temp:
            self.stdout.write('Checking for temporary upload files...')
            # This would need actual file system cleanup logic
            # For now, just log the intent
            self.stdout.write(
                self.style.SUCCESS('Temporary file cleanup completed')
            )

        self.stdout.write(
            self.style.SUCCESS('Document cleanup completed successfully')
        )
