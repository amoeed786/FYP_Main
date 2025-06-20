# Generated by Django 4.2.7 on 2025-04-29 19:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('examigo', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SemesterPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='semester_plans', to='examigo.document')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='semester_plans', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
