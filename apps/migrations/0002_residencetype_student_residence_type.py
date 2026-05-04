from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


def migrate_residence_types(apps, schema_editor):
    Menu = apps.get_model('apps', 'Menu')
    ResidenceType = apps.get_model('apps', 'ResidenceType')
    Student = apps.get_model('apps', 'Student')

    now = timezone.now()
    Menu.objects.get_or_create(
        menu_id='JENIS-TINGGAL',
        defaults={
            'menu_name': 'Jenis Tinggal',
            'menu_remark': 'Master jenis tinggal santri',
            'entry_date': now,
            'entry_by': 'migration',
            'update_date': now,
            'update_by': 'migration',
        },
    )

    normalized_map = {}
    for student in Student.objects.all():
        raw_name = (student.residence_type or '').strip()
        display_name = raw_name or 'Belum Diisi'
        normalized_name = display_name.lower()

        residence_type = normalized_map.get(normalized_name)
        if residence_type is None:
            residence_type = ResidenceType.objects.create(
                residence_type_name=display_name,
                entry_date=now,
                entry_by='migration',
                update_date=now,
                update_by='migration',
            )
            normalized_map[normalized_name] = residence_type

        Student.objects.filter(student_id=student.student_id).update(
            residence_type_master_id=residence_type.residence_type_id)


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResidenceType',
            fields=[
                ('residence_type_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('residence_type_name', models.CharField(max_length=50, unique=True)),
                ('entry_date', models.DateTimeField(null=True)),
                ('entry_by', models.CharField(max_length=50, null=True)),
                ('update_date', models.DateTimeField(blank=True, null=True)),
                ('update_by', models.CharField(blank=True, max_length=50, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='student',
            name='residence_type_master',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='apps.residencetype'),
        ),
        migrations.RunPython(migrate_residence_types, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='student',
            name='residence_type',
        ),
        migrations.RenameField(
            model_name='student',
            old_name='residence_type_master',
            new_name='residence_type',
        ),
        migrations.AlterField(
            model_name='student',
            name='residence_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='apps.residencetype'),
        ),
    ]
