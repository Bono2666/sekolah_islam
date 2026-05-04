from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0004_hostel_student_hostel'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='hostel',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='apps.hostel'),
        ),
    ]
