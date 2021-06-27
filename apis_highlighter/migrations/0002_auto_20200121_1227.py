# Generated by Django 2.1.12 on 2020-01-21 12:27

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('apis_metainfo', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('apis_highlighter', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='annotation',
            name='entity_candidate',
            field=models.ManyToManyField(blank=True, to='apis_metainfo.UriCandidate'),
        ),
        migrations.AddField(
            model_name='annotation',
            name='entity_link',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='annotation',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='parent_annotation', to='apis_highlighter.Annotation'),
        ),
        migrations.AddField(
            model_name='annotation',
            name='text',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apis_metainfo.Text'),
        ),
        migrations.AddField(
            model_name='annotation',
            name='user_added',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
