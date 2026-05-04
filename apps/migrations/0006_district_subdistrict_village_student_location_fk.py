from django.db import migrations, models
import django.db.models.deletion


def forwards(apps, schema_editor):
    District = apps.get_model('apps', 'District')
    SubDistrict = apps.get_model('apps', 'SubDistrict')
    Village = apps.get_model('apps', 'Village')
    Student = apps.get_model('apps', 'Student')

    for student in Student.objects.all():
        district_name = (student.district_legacy or '').strip()
        sub_district_name = (student.sub_district_legacy or '').strip()
        village_name = (student.village_legacy or '').strip()

        district, _ = District.objects.get_or_create(
            district_name=district_name or '-'
        )
        sub_district, _ = SubDistrict.objects.get_or_create(
            district=district,
            sub_district_name=sub_district_name or '-'
        )
        village, _ = Village.objects.get_or_create(
            sub_district=sub_district,
            village_name=village_name or '-'
        )

        student.district = district
        student.sub_district = sub_district
        student.village = village
        student.save(update_fields=['district', 'sub_district', 'village'])


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0005_alter_student_hostel'),
    ]

    operations = [
        migrations.CreateModel(
            name='District',
            fields=[
                ('district_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('district_name', models.CharField(max_length=100, unique=True)),
                ('entry_date', models.DateTimeField(null=True)),
                ('entry_by', models.CharField(max_length=50, null=True)),
                ('update_date', models.DateTimeField(blank=True, null=True)),
                ('update_by', models.CharField(blank=True, max_length=50, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SubDistrict',
            fields=[
                ('sub_district_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('sub_district_name', models.CharField(max_length=100)),
                ('entry_date', models.DateTimeField(null=True)),
                ('entry_by', models.CharField(max_length=50, null=True)),
                ('update_date', models.DateTimeField(blank=True, null=True)),
                ('update_by', models.CharField(blank=True, max_length=50, null=True)),
                ('district', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='apps.district')),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('district', 'sub_district_name'), name='unique_sub_district_per_district')],
            },
        ),
        migrations.CreateModel(
            name='Village',
            fields=[
                ('village_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('village_name', models.CharField(max_length=100)),
                ('entry_date', models.DateTimeField(null=True)),
                ('entry_by', models.CharField(max_length=50, null=True)),
                ('update_date', models.DateTimeField(blank=True, null=True)),
                ('update_by', models.CharField(blank=True, max_length=50, null=True)),
                ('sub_district', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='apps.subdistrict')),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('sub_district', 'village_name'), name='unique_village_per_sub_district')],
            },
        ),
        migrations.RenameField(
            model_name='student',
            old_name='district',
            new_name='district_legacy',
        ),
        migrations.RenameField(
            model_name='student',
            old_name='sub_district',
            new_name='sub_district_legacy',
        ),
        migrations.RenameField(
            model_name='student',
            old_name='village',
            new_name='village_legacy',
        ),
        migrations.AddField(
            model_name='student',
            name='district',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='apps.district'),
        ),
        migrations.AddField(
            model_name='student',
            name='sub_district',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='apps.subdistrict'),
        ),
        migrations.AddField(
            model_name='student',
            name='village',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='apps.village'),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='student',
            name='district_legacy',
        ),
        migrations.RemoveField(
            model_name='student',
            name='sub_district_legacy',
        ),
        migrations.RemoveField(
            model_name='student',
            name='village_legacy',
        ),
        migrations.AlterField(
            model_name='student',
            name='district',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='apps.district'),
        ),
        migrations.AlterField(
            model_name='student',
            name='sub_district',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='apps.subdistrict'),
        ),
        migrations.AlterField(
            model_name='student',
            name='village',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='apps.village'),
        ),
    ]
