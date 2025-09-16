"""
Management command to handle circular dependency issues with django-document-manager
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import migrations
from django.apps import apps
from django.conf import settings


class Command(BaseCommand):
    help = 'Migrate django-document-manager with circular dependency handling'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-user-deps',
            action='store_true',
            help='Skip user-related foreign key creation if circular dependency detected',
        )
        parser.add_argument(
            '--app',
            type=str,
            help='Specific app to check for circular dependencies',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually running migrations',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Checking for circular dependencies with django-document-manager...')
        )
        
        # Check for potential circular dependencies
        circular_deps = self.detect_circular_dependencies(options.get('app'))
        
        if circular_deps:
            self.stdout.write(
                self.style.WARNING(f'Detected potential circular dependencies: {circular_deps}')
            )
            
            if options['skip_user_deps']:
                self.stdout.write(
                    self.style.WARNING('Skipping user foreign key creation to avoid circular dependencies')
                )
                self.migrate_without_user_deps(options['dry_run'])
            else:
                self.stdout.write(
                    self.style.ERROR(
                        'Circular dependency detected. Use --skip-user-deps to migrate without user foreign keys, '
                        'then add them manually later.'
                    )
                )
                return
        else:
            self.stdout.write(self.style.SUCCESS('No circular dependencies detected'))
            self.migrate_normally(options['dry_run'])

    def detect_circular_dependencies(self, specific_app=None):
        """
        Detect potential circular dependencies between apps
        """
        circular_deps = []
        
        try:
            # Get all apps that might have BaseDocumentOwnerModel subclasses
            for app_config in apps.get_app_configs():
                if specific_app and app_config.label != specific_app:
                    continue
                    
                # Check if app has models that inherit from BaseDocumentOwnerModel
                try:
                    models = app_config.get_models()
                    for model in models:
                        # Check if model inherits from BaseDocumentOwnerModel
                        from django_document_manager.models import BaseDocumentOwnerModel
                        if issubclass(model, BaseDocumentOwnerModel) and model != BaseDocumentOwnerModel:
                            # Check if this app also has migrations that depend on auth
                            migration_files = self.get_app_migration_dependencies(app_config.label)
                            if 'auth' in migration_files or settings.AUTH_USER_MODEL.split('.')[0] in migration_files:
                                circular_deps.append(app_config.label)
                                
                except Exception:
                    # Skip apps that can't be loaded
                    continue
                    
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Error detecting circular dependencies: {e}'))
            
        return circular_deps

    def get_app_migration_dependencies(self, app_label):
        """
        Get migration dependencies for an app
        """
        dependencies = set()
        try:
            migration_loader = migrations.loader.MigrationLoader(connection=None)
            for migration in migration_loader.graph.nodes:
                if migration[0] == app_label:
                    migration_obj = migration_loader.get_migration(*migration)
                    for dep in migration_obj.dependencies:
                        dependencies.add(dep[0])
        except Exception:
            pass
        return dependencies

    def migrate_without_user_deps(self, dry_run=False):
        """
        Migrate django-document-manager without user dependencies
        """
        from django.core.management import call_command
        
        self.stdout.write('Running migration without user foreign keys...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN: Would run initial migration without user deps'))
            return
            
        try:
            # Run only the first migration (without user deps)
            call_command('migrate', 'django_document_manager', '0001', verbosity=2)
            
            self.stdout.write(
                self.style.SUCCESS(
                    'Base django-document-manager models created. '
                    'Run "python manage.py migrate django_document_manager 0002" '
                    'after resolving circular dependencies to add user relationships.'
                )
            )
        except Exception as e:
            raise CommandError(f'Migration failed: {e}')

    def migrate_normally(self, dry_run=False):
        """
        Run normal migration
        """
        from django.core.management import call_command
        
        self.stdout.write('Running normal migration...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN: Would run full migration'))
            return
            
        try:
            call_command('migrate', 'django_document_manager', verbosity=2)
            self.stdout.write(self.style.SUCCESS('Migration completed successfully'))
        except Exception as e:
            raise CommandError(f'Migration failed: {e}')