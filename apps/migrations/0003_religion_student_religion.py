from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


def migrate_religions(apps, schema_editor):
    Menu = apps.get_model('apps', 'Menu')
    Religion = apps.get_model('apps', 'Religion')
    Student = apps.get_model('apps', 'Student')

    now = timezone.now()
    Menu.objects.get_or_create(
        menu_id='AGAMA',
        defaults={
            'menu_name': 'Agama',
            'menu_remark': 'Master agama santri',
            'entry_date': now,
            'entry_by': 'migration',
            'update_date': now,
            'update_by': 'migration',
        },
    )

    normalized_map = {}
    for student in Student.objects.all():
        raw_name = (student.religion or '').strip()
        if not raw_name:
            continue

        normalized_name = raw_name.lower()
        religion = normalized_map.get(normalized_name)
        if religion is None:
            religion, _ = Religion.objects.get_or_create(
                religion_name=raw_name,
                defaults={
                    'entry_date': now,
                    'entry_by': 'migration',
                    'update_date': now,
                    'update_by': 'migration',
                },
            )
            normalized_map[normalized_name] = religion

        Student.objects.filter(student_id=student.student_id).update(
            religion_master_id=religion.religion_id)


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0002_residencetype_student_residence_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='Religion',
            fields=[
                ('religion_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('religion_name', models.CharField(max_length=50, unique=True)),
                ('entry_date', models.DateTimeField(null=True)),
                ('entry_by', models.CharField(max_length=50, null=True)),
                ('update_date', models.DateTimeField(blank=True, null=True)),
                ('update_by', models.CharField(blank=True, max_length=50, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='student',
            name='religion_master',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='apps.religion'),
        ),
        migrations.RunPython(migrate_religions, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='student',
            name='religion',
        ),
        migrations.RenameField(
            model_name='student',
            old_name='religion_master',
            new_name='religion',
        ),
    ]
