from django.db import migrations
from django.utils import timezone


def create_menu(apps, schema_editor):
    Menu = apps.get_model('apps', 'Menu')
    now = timezone.now()
    Menu.objects.get_or_create(
        menu_id='NILAI-KELAS',
        defaults={
            'menu_name': 'Nilai Per Kelas',
            'menu_remark': 'Penilaian per mapel per kelas per guru',
            'entry_date': now,
            'entry_by': 'migration',
            'update_date': now,
            'update_by': 'migration',
        },
    )


def remove_menu(apps, schema_editor):
    Menu = apps.get_model('apps', 'Menu')
    Menu.objects.filter(menu_id='NILAI-KELAS').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0037_studentscore'),
    ]

    operations = [
        migrations.RunPython(create_menu, remove_menu),
    ]
