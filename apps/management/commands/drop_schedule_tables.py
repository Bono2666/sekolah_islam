"""
Management command: drop_schedule_tables

Menghapus tabel schedule dan indeksnya dari database.

Cara pakai:
  python manage.py drop_schedule_tables

  # Atau tanpa konfirmasi:
  python manage.py drop_schedule_tables --force
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Menghapus tabel schedule dan indeksnya dari database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip konfirmasi',
        )

    def handle(self, *args, **options):
        force = options['force']

        tables_to_drop = [
            'apps_schedule',
        ]

        indexes_to_drop = [
            'apps_schedule_grade_day_idx',
            'apps_schedule_teacher_day_idx',
            'apps_schedule_day_start_time_end_time_idx',
        ]

        if not force:
            self.stdout.write(self.style.WARNING('\nPeringatan: Ini akan menghapus tabel berikut dari database:'))
            for t in tables_to_drop:
                self.stdout.write(f'  - {t}')
            for i in indexes_to_drop:
                self.stdout.write(f'  - {i} (indeks)')

            confirm = input('\nLanjutkan? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Dibatalkan.'))
                return

        with connection.cursor() as cursor:
            # Drop indexes first
            for idx in indexes_to_drop:
                try:
                    cursor.execute(f"DROP INDEX IF EXISTS `{idx}` ON `apps_schedule`")
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Indeks "{idx}" dihapus'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  ~ Indeks "{idx}": {e}'))

            # Drop table
            for table in tables_to_drop:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Tabel "{table}" dihapus'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ Tabel "{table}": {e}'))

        self.stdout.write(self.style.SUCCESS('\n✓ Selesai menghapus tabel schedule.'))
