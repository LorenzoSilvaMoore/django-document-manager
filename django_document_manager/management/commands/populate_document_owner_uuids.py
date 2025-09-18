"""
Management command to populate document_owner_uuid for existing instances
that inherit from BaseDocumentOwnerModel.

This command is useful when:
1. Adding BaseDocumentOwnerModel inheritance to an existing model with data
2. After migrations to ensure all instances have UUIDs
3. Recovery scenarios where UUIDs might be missing

Usage:
    python manage.py populate_document_owner_uuids
    python manage.py populate_document_owner_uuids --model myapp.MyModel
    python manage.py populate_document_owner_uuids --dry-run
    python manage.py populate_document_owner_uuids --batch-size 100
"""

import logging
import time
from typing import List, Type

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from django.apps import apps
from django.db.models import Model
from django.conf import settings

from django_document_manager.models.models import BaseDocumentOwnerModel

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Populate document_owner_uuid for existing BaseDocumentOwnerModel instances'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            help='Specific model to update in format "app_label.ModelName" (e.g., "myapp.Company")'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of records to process in each batch (default: 100)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output showing each record processed'
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.batch_size = options['batch_size']
        self.verbose_output = options['verbose']
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )

        try:
            if options['model']:
                # Update specific model
                model_class = self._get_model_class(options['model'])
                self._update_model(model_class)
            else:
                # Update all models that inherit from BaseDocumentOwnerModel
                models_to_update = self._find_document_owner_models()
                
                if not models_to_update:
                    self.stdout.write(
                        self.style.SUCCESS(
                            'No models found that inherit from BaseDocumentOwnerModel'
                        )
                    )
                    return

                for model_class in models_to_update:
                    self._update_model(model_class)

            self.stdout.write(
                self.style.SUCCESS('Successfully completed UUID population')
            )

        except Exception as e:
            logger.exception("Error in populate_document_owner_uuids command")
            raise CommandError(f"Command failed: {str(e)}")

    def _get_model_class(self, model_path: str) -> Type[Model]:
        """
        Get model class from string path like 'app_label.ModelName'
        """
        try:
            app_label, model_name = model_path.split('.', 1)
            model_class = apps.get_model(app_label, model_name)
            
            if not issubclass(model_class, BaseDocumentOwnerModel):
                raise CommandError(
                    f"Model {model_path} does not inherit from BaseDocumentOwnerModel"
                )
            
            return model_class
            
        except ValueError:
            raise CommandError(
                f"Invalid model format: {model_path}. Use 'app_label.ModelName'"
            )
        except LookupError:
            raise CommandError(f"Model not found: {model_path}")

    def _find_document_owner_models(self) -> List[Type[Model]]:
        """
        Find all concrete models that inherit from BaseDocumentOwnerModel
        """
        owner_models = []
        
        for model in apps.get_models():
            if (issubclass(model, BaseDocumentOwnerModel) and 
                not model._meta.abstract):
                owner_models.append(model)
        
        return owner_models

    def _update_model(self, model_class: Type[Model]):
        """
        Update all instances of a model that don't have document_owner_uuid
        """
        model_name = f"{model_class._meta.app_label}.{model_class._meta.model_name}"
        
        # Get count of instances without UUIDs
        instances_without_uuid = model_class.objects.filter(
            document_owner_uuid__isnull=True
        )
        total_count = instances_without_uuid.count()
        
        if total_count == 0:
            self.stdout.write(
                f"✓ {model_name}: All instances already have UUIDs"
            )
            return

        self.stdout.write(
            f"📋 {model_name}: Found {total_count} instances without UUIDs"
        )

        if self.dry_run:
            self.stdout.write(
                f"   Would update {total_count} instances (DRY RUN)"
            )
            return

        # Process in batches to avoid memory issues
        updated_count = 0
        start_time = time.time()
        
        while True:
            with transaction.atomic():
                # Get a batch of instances without UUIDs
                batch = list(
                    instances_without_uuid[:self.batch_size]
                )
                
                if not batch:
                    break
                
                # Update each instance in the batch
                for instance in batch:
                    try:
                        # The save method will automatically generate UUID
                        instance.save(update_fields=['document_owner_uuid'])
                        updated_count += 1
                        
                        if self.verbose_output:
                            self.stdout.write(
                                f"   Updated {model_name} ID {instance.pk}: "
                                f"{instance.document_owner_uuid}"
                            )
                            
                    except Exception as e:
                        logger.error(
                            f"Error updating {model_name} ID {instance.pk}: {e}"
                        )
                        self.stdout.write(
                            self.style.ERROR(
                                f"   ✗ Failed to update ID {instance.pk}: {e}"
                            )
                        )

                # Progress update for large datasets
                if updated_count % (self.batch_size * 10) == 0:
                    self.stdout.write(f"   Progress: {updated_count}/{total_count}")

        elapsed = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS(
                f"✓ {model_name}: Updated {updated_count} instances "
                f"in {elapsed:.2f} seconds"
            )
        )

        # Verify the update
        remaining_count = model_class.objects.filter(
            document_owner_uuid__isnull=True
        ).count()
        
        if remaining_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠ {model_name}: {remaining_count} instances still without UUIDs"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ {model_name}: All instances now have UUIDs"
                )
            )