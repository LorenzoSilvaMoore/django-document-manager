from django.core.management.base import BaseCommand
from django.db import connection
from pathlib import Path
import os

class Command(BaseCommand):
    help = 'Load geographic data from SQL file into the database'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get the path to the data directory relative to this file
        current_dir = Path(__file__).parent.parent.parent
        self.data_dir = current_dir / 'data'
        self.sql_file = self.data_dir / 'world.sql'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sql-file',
            type=str,
            default=None,
            help='Path to the SQL file to execute (defaults to data/example_world.sql)'
        )
        parser.add_argument(
            '--database',
            type=str,
            default='default',
            help='Database alias to use (defaults to "default")'
        )

    def handle(self, *args, **options):
        # Determine which SQL file to use
        sql_file = options['sql_file']
        if sql_file:
            sql_file = Path(sql_file)
        else:
            sql_file = self.sql_file

        if not sql_file.exists():
            self.stdout.write(
                self.style.ERROR(f'SQL file not found: {sql_file}')
            )
            return

        database_alias = options['database']
        
        self.stdout.write(
            self.style.SUCCESS(f'Loading data from {sql_file} into database "{database_alias}"...')
        )

        try:
            # Read the SQL file
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # Get database connection
            with connection.cursor() as cursor:
                # Execute the SQL content
                cursor.execute(sql_content)
                
            self.stdout.write(
                self.style.SUCCESS('Geographic data loaded successfully from SQL file!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error executing SQL file: {str(e)}')
            )
            raise