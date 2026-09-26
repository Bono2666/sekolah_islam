from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0028_gradesubject'),
    ]

    operations = [
        migrations.AddField(
            model_name='teachersubject',
            name='grade_subject',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='teacher_subjects',
                to='apps.gradesubject',
            ),
        ),
        migrations.RemoveField(
            model_name='teachersubject',
            name='grade',
        ),
        migrations.RemoveField(
            model_name='teachersubject',
            name='subject',
        ),
        migrations.AlterUniqueTogether(
            name='teachersubject',
            unique_together={('grade_subject', 'teacher')},
        ),
    ]
