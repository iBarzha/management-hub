# Generated by Django 5.2.4 on 2025-07-25 15:52

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium', max_length=20)),
                ('status', models.CharField(choices=[('todo', 'To Do'), ('in_progress', 'In Progress'), ('review', 'Review'), ('done', 'Done')], default='todo', max_length=20)),
                ('due_date', models.DateTimeField(blank=True, null=True)),
                ('estimated_hours', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('actual_hours', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'tasks',
                'ordering': ['-created_at'],
            },
        ),
    ]
