from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


def migrate_hostels(apps, schema_editor):
    Menu = apps.get_model('apps', 'Menu')
    Hostel = apps.get_model('apps', 'Hostel')
    Student = apps.get_model('apps', 'Student')

    now = timezone.now()
    Menu.objects.get_or_create(
        menu_id='ASRAMA',
        defaults={
            'menu_name': 'Asrama',
            'menu_remark': 'Master asrama santri',
            'entry_date': now,
            'entry_by': 'migration',
            'update_date': now,
            'update_by': 'migration',
        },
    )

    normalized_map = {}
    for student in Student.objects.all():
        raw_name = (student.hostel or '').strip()
        display_name = raw_name or 'Belum Diisi'
        normalized_name = display_name.lower()

        hostel = normalized_map.get(normalized_name)
        if hostel is None:
            hostel, _ = Hostel.objects.get_or_create(
                hostel_name=display_name,
                defaults={
                    'entry_date': now,
                    'entry_by': 'migration',
                    'update_date': now,
                    'update_by': 'migration',
                },
            )
            normalized_map[normalized_name] = hostel

        Student.objects.filter(student_id=student.student_id).update(
            hostel_master_id=hostel.hostel_id)


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0003_religion_student_religion'),
    ]

    operations = [
        migrations.CreateModel(
            name='Hostel',
            fields=[
                ('hostel_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('hostel_name', models.CharField(max_length=50, unique=True)),
                ('entry_date', models.DateTimeField(null=True)),
                ('entry_by', models.CharField(max_length=50, null=True)),
                ('update_date', models.DateTimeField(blank=True, null=True)),
                ('update_by', models.CharField(blank=True, max_length=50, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='student',
            name='hostel_master',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='apps.hostel'),
        ),
        migrations.RunPython(migrate_hostels, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='student',
            name='hostel',
        ),
        migrations.RenameField(
            model_name='student',
            old_name='hostel_master',
            new_name='hostel',
        ),
        migrations.AlterField(
            model_name='student',
            name='hostel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='apps.hostel'),
        ),
    ]
