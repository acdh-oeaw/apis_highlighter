# Generated by Django 2.1.12 on 2020-01-21 12:27

import django.db.models.deletion
import gm2m.fields
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
            field=gm2m.fields.GM2MField('apis_entities.Person', 'apis_entities.Institution', 'apis_entities.Place', 'apis_entities.Event', 'apis_entities.Work', 'apis_relations.PersonPerson', 'apis_relations.PersonPlace', 'apis_relations.PersonInstitution', 'apis_relations.PersonEvent', 'apis_relations.PersonWork', 'apis_relations.InstitutionPlace', 'apis_relations.InstitutionEvent', 'apis_relations.InstitutionWork', 'apis_relations.InstitutionInstitution', 'apis_relations.PlaceEvent', 'apis_relations.PlaceWork', 'apis_relations.PlacePlace', 'apis_relations.EventWork', 'apis_relations.EventEvent', 'apis_relations.WorkWork', through_fields=('gm2m_src', 'gm2m_tgt', 'gm2m_ct', 'gm2m_pk')),
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
