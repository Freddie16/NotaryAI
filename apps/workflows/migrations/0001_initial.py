# Generated by Django 5.2 on 2025-05-08 09:22

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('clients', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkflowTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Matter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('protocol_number', models.CharField(max_length=100, unique=True)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('status', models.CharField(choices=[('open', 'Open'), ('in_progress', 'In Progress'), ('on_hold', 'On Hold'), ('closed', 'Closed'), ('cancelled', 'Cancelled')], default='open', max_length=20)),
                ('start_date', models.DateField(auto_now_add=True)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('completion_date', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_users', models.ManyToManyField(blank=True, related_name='assigned_matters', to=settings.AUTH_USER_MODEL)),
                ('clients', models.ManyToManyField(related_name='matters', to='clients.client')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_matters', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['protocol_number'],
            },
        ),
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('not_started', 'Not Started'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='not_started', max_length=20)),
                ('initiated_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('ai_generated_steps', models.JSONField(blank=True, help_text='AI-generated list of steps', null=True)),
                ('matter', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='workflow', to='workflows.matter')),
                ('template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='workflows.workflowtemplate')),
            ],
        ),
        migrations.CreateModel(
            name='WorkflowStepTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('order', models.PositiveIntegerField(default=0)),
                ('is_required', models.BooleanField(default=True)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='step_templates', to='workflows.workflowtemplate')),
            ],
            options={
                'ordering': ['order'],
                'unique_together': {('template', 'order')},
            },
        ),
        migrations.CreateModel(
            name='WorkflowStep',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('order', models.PositiveIntegerField(default=0)),
                ('status', models.CharField(choices=[('not_started', 'Not Started'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('skipped', 'Skipped')], default='not_started', max_length=20)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_workflow_steps', to=settings.AUTH_USER_MODEL)),
                ('workflow', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='steps', to='workflows.workflow')),
                ('step_template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='workflows.workflowsteptemplate')),
            ],
            options={
                'ordering': ['order'],
                'unique_together': {('workflow', 'order')},
            },
        ),
        migrations.AddConstraint(
            model_name='workflow',
            constraint=models.UniqueConstraint(fields=('matter',), name='unique_matter_workflow'),
        ),
    ]
