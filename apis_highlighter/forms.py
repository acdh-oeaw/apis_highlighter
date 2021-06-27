from django import forms
#import autocomplete_light.shortcuts as al
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.layout import Submit
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Group
from django.db.models.fields import BLANK_CHOICE_DASH
from apis_core.apis_entities.fields import ModelSelect2
from django.urls import reverse
from apis_core.apis_entities.fields import ListSelect2


#from relations.forms import PersonPlaceForm, PersonInstitutionForm
from apis_core.apis_metainfo.models import Collection
from .models import AnnotationProject, Annotation
from apis_core.apis_vocabularies.models import TextType
from dal import autocomplete
from django.conf import settings



class LinkHighlighterForm(forms.Form):

    #relation = forms.CharField(label='Relation', widget=al.TextWidget('PersonAutocomplete'))
    relation = forms.CharField(label='Relation')


class SelectAnnotationProject(forms.Form):
    project = forms.ChoiceField(label=False, required=False)
    users_show = forms.MultipleChoiceField(label=False, required=False)
    #show_all = forms.BooleanField(label='Show all?')

    def __init__(self, *args, **kwargs):
        choices_type = getattr(settings, 'APIS_HIGHLIGHTER_MODELS', None)
        if choices_type is None:
            choices_type = ContentType.objects.filter(app_label__in=['apis_entities', 'apis_relations']).values_list('pk', 'model')
        set_ann_proj = kwargs.pop('set_ann_proj', False)
        entity_types_highlighter = kwargs.pop('entity_types_highlighter', False)
        users_show = kwargs.pop('users_show_highlighter', False)
        super().__init__(*args, **kwargs)
        CHOICES = AnnotationProject.objects.all()
        choices_user = User.objects.all()
        self.fields['project'] = forms.ChoiceField(
            choices=tuple((x.pk, x.name) for x in CHOICES),
            label=False)
        self.fields['users_show'] = forms.MultipleChoiceField(
            choices=tuple((x.pk, x.username) for x in choices_user),
            label=False)
        self.fields['types'] = forms.MultipleChoiceField(required=False, choices=choices_type, label=False)
        self.helper = FormHelper()
        self.helper.form_id = 'InitAnnotationProject'
        self.helper.form_class = 'form-inline'
        self.helper.form_method = 'GET'
        self.initial['project'] = set_ann_proj
        self.initial['types'] = entity_types_highlighter
        self.initial['users_show'] = users_show
        self.helper.add_input(Submit('Update', 'Update'))


class SelectAnnotatorAgreement(forms.Form):
    choices_metrics = (('Do_alpha', 'Disagreement Alpha Coefficient'),
                       ('multi_kappa', 'Multi Kappa (Davies and Fleiss 1982)'),
                       ('alpha', 'Krippendorff 1980'),
                       ('avg_Ao', 'Average observed agreement'),
                       ('S', 'Bennett, Albert and Goldstein 1954'),
                       ('pi', 'Scott 1955; here, multi-pi.'),
                       ('kappa', 'Kappa (Cohen 1960)'),
                       ('weighted_kappa', 'Weighted Kappa (Cohen 1968)'))
    choices_format_string = (('start_end_text', 'String & Annotation'),
                             ('start_end_text_ent', 'String, Annotation & Entity type'),
                             ('start_end_text_ent_entid', 'String, Annotation, Entity type & ID'),
                             ('start_end_text_rel_ent_entid', 'String, Annotation, Entity type, ID & relation type'))
    metrics = forms.ChoiceField(label='Metrics', choices=choices_metrics, required=True)
    format_string = forms.ChoiceField(label='Format Annotation', choices=choices_format_string, required=True)
    user_group = forms.ChoiceField(label='User group', required=False)
    gold_standard = forms.ChoiceField(label='Gold standard', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices_groups = Group.objects.all()
        choices_users = User.objects.all()
        self.fields['user_group'] = forms.ChoiceField(
            choices=BLANK_CHOICE_DASH+list((x.pk, x.name) for x in choices_groups),
            required=False)
        self.fields['gold_standard'] = forms.ChoiceField(
            choices=BLANK_CHOICE_DASH+list((x.pk, x.username) for x in choices_users),
            required=False)
        self.helper = FormHelper()
        self.helper.form_id = 'SelectAnnotatorAgreement'
        self.helper.form_class = 'form-inline'
        self.helper.form_method = 'GET'
        self.helper.add_input(Submit('Update', 'Update'))


class SelectAnnotatorAgreementCollection(SelectAnnotatorAgreement):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['anno_proj'] = forms.ChoiceField(
            label='Annotation Project',
            choices=list((x.pk, x.name) for x in AnnotationProject.objects.all()),
            required=True)
        self.fields['collection'] = forms.ChoiceField(
            choices=BLANK_CHOICE_DASH + list((x.pk, x.name) for x in Collection.objects.all()),
            required=False)
        self.fields['kind_instance'] = forms.ChoiceField(label='Entity kind Collection',
            choices=BLANK_CHOICE_DASH + list((x.pk, x.name) for x in ContentType.objects.filter(app_label="entities")),
            required=False)
        self.fields['text_type'] = forms.MultipleChoiceField(
            choices=BLANK_CHOICE_DASH + list((x.pk, x.name) for x in TextType.objects.all()),
            required=False)
        self.helper.form_id = 'SelectAnnotatorAgreementCollection'
        self.helper.form_class = 'form'
        self.helper.form_method = 'POST'
        self.order_fields(('metrics', 'anno_proj', 'format_string', 'user_group',
                                'gold_standard', 'collection', 'kind_instance', 'text_type'))


class BaseEntityHighlighterForm(forms.Form):
    HL_start = forms.IntegerField(widget=forms.HiddenInput)
    HL_end = forms.IntegerField(widget=forms.HiddenInput)
    HL_text_id = forms.CharField(widget=forms.HiddenInput)
    HL_id = forms.CharField(widget=forms.HiddenInput, required=False)

    def save(self, *args, **kwargs):
        cd = self.cleaned_data
        txt = ContentType.objects.get(app_label='apis_metainfo', model='text').model_class().objects.get(pk=cd['HL_text_id'][5:])
        if cd['HL_id']:
            a = Annotation.objects.get(pk=cd['HL_id'])
            a.user_added = self.request.user
            a.annotation_project_id = int(self.request.session.get('annotation_project', 1))
        else:
            a = Annotation(
                start=cd['HL_start'],
                end=cd['HL_end'],
                text=txt,
                user_added=self.request.user,
                annotation_project_id=int(self.request.session.get('annotation_project', 1)))
        a.save()
        return a

    def __init__(self, *args, **kwargs):
        self.entity_type = kwargs.pop('entity_type', False)
        self.request = kwargs.pop('request', False)
        self.instance = kwargs.pop('instance', False)
        siteID = kwargs.pop('siteID', False)
        super(BaseEntityHighlighterForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['HL_id'].initial = self.instance
        self.helper = FormHelper()
        self.helper.form_tag = False

    def get_text_id(self):
        return self.cleaned_data['HL_text_id'][5:]


class PersonHighlighterForm(BaseEntityHighlighterForm):
    person = forms.CharField(label='Person')
    person_uri = forms.CharField(required=False, widget=forms.HiddenInput())

    def save(self, *args, **kwargs):
        x = super(PersonHighlighterForm, self).save(*args, **kwargs)
        cd = self.cleaned_data
        p = Person.get_or_create_uri(cd['person_uri'])
        if not p:
            p = GenericRDFParser(cd['person_uri'], 'Person').get_or_create()
        x.entity_link = p
        x.save()
        return p

    def __init__(self, *args, **kwargs):
        super(PersonHighlighterForm, self).__init__(*args, **kwargs)
        self.helper.form_class = 'PersonEntityForm'
        if self.instance:
            a = self.instance
            ent = a.entity_link
            self.fields['person'].initial = ent.name+', '+ent.first_name
            self.fields['person_uri'].initial = Uri.objects.filter(entity=ent)[0].uri


class PlaceHighlighterForm(BaseEntityHighlighterForm):
    place = forms.CharField(label='Place')
    place_uri = forms.CharField(required=False, widget=forms.HiddenInput())

    def save(self, *args, **kwargs):
        x = super(PlaceHighlighterForm, self).save(*args, **kwargs)
        cd = self.cleaned_data
        p = Place.get_or_create_uri(cd['place_uri'])
        if not p:
            p = GenericRDFParser(cd['place_uri'], 'Place').get_or_create()
        x.entity_link = p
        x.save()
        return p

    def __init__(self, *args, **kwargs):
        super(PlaceHighlighterForm, self).__init__(*args, **kwargs)
        self.helper.form_class = 'PlaceEntityForm'
        if self.instance:
            a = self.instance
            ent = a.entity_link
            self.fields['place'].initial = ent.name
            self.fields['place_uri'].initial = Uri.objects.filter(entity=ent)[0].uri


class SundayHighlighterForm(BaseEntityHighlighterForm):

    def save(self, *args, **kwargs):
        x = super(SundayHighlighterForm, self).save(*args, **kwargs)
        cd = self.cleaned_data
        p = ContentType.objects.get(app_label='apis_vocabularies', model='sundayrepresentations').model_class().objects.get(pk=cd['sunday_rep'])
        x.entity_link = p
        x.save()
        return p

    def __init__(self, *args, **kwargs):
        super(SundayHighlighterForm, self).__init__(*args, **kwargs)
        attrs = {'data-placeholder': 'Type to get suggestions',
                 'data-minimum-input-length': 3,
                 'data-html': True,
                 'style': 'width: 100%'}
        self.fields['sunday_rep'] = autocomplete.Select2ListCreateChoiceField(
                label='Relation type',
                widget=ListSelect2(
                    #url='/vocabularies/autocomplete/{}{}relation/normal'.format(lst_src_target[0].lower(), lst_src_target[1].lower()),
                    url=reverse('apis:apis_vocabularies:generic_vocabularies_autocomplete', args=['sundayrepresentations', 'normal']),
                    attrs=attrs))

        if self.instance:
            a = self.instance
            ent = a.entity_link
            self.fields['sunday_rep'].initial = (ent.pk, ent.name)


class PlaceEntityHighlighterForm(forms.Form):
    place = forms.CharField(label='Place', widget=ModelSelect2(url='autocomplete/place'))
    place_uri = forms.CharField(required=False, widget=forms.HiddenInput())
    HL_start = forms.IntegerField(widget=forms.HiddenInput)
    HL_end = forms.IntegerField(widget=forms.HiddenInput)
    HL_text_id = forms.CharField(widget=forms.HiddenInput)

    def save(self, *args, **kwargs):
        cd = self.cleaned_data
        pl = Place.get_or_create_uri(cd['place_uri'])
        if not pl:
            pl = GenericRDFParser(cd['place_uri'], 'Place').get_or_create()
        txt = Text.objects.get(pk=cd['HL_text_id'][5:])
        a = Annotation(
            start=cd['HL_start'],
            end=cd['HL_end'],
            text=txt,
            user_added=self.request.user,
            annotation_project_id=int(self.request.session.get('annotation_project', 1)))
        a.entity_link = pl
        a.save()
        return a

    def __init__(self, *args, **kwargs):
        entity_type = kwargs.pop('entity_type', False)
        self.request = kwargs.pop('request', False)
        super(PlaceEntityHighlighterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'PlaceEntityForm'
        self.helper.form_tag = False


class AddRelationHighlighterBaseForm(forms.Form):
    HL_start = forms.IntegerField(widget=forms.HiddenInput)
    HL_end = forms.IntegerField(widget=forms.HiddenInput)
    HL_text_id = forms.CharField(widget=forms.HiddenInput)
    RL_type = forms.CharField(widget=forms.HiddenInput)
    RL_pk = forms.IntegerField(widget=forms.HiddenInput)

    def save(self):
        cd = self.cleaned_data
        #x = super(AddRelationHighlighterBaseForm, self).save()
        txt = Text.objects.get(pk=cd['HL_text_id'][5:])
        ent = ContentType.objects.get(
            pk=cd['RL_type']).model_class().objects.get(pk=cd['RL_pk'])
        self.ann = Annotation(
            start=cd['HL_start'],
            end=cd['HL_end'],
            text=txt,
            user_added=self.request.user)
        self.ann.entity_link = ent
        self.ann.save()
        return self.ann


class AddRelationHighlighterPersonForm(AddRelationHighlighterBaseForm):
    # relation = forms.CharField(
    #     label='Relation',
    #     widget=al.TextWidget('AddRelationPersonHighlighterAutocomplete'),
    #     )

    def save(self, *args, **kwargs):
        cd = self.cleaned_data
        x = super().save()

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', False)
        self.entity_type = kwargs.pop('entity_type', False)
        super(AddRelationHighlighterPersonForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    def get_text_id(self):
        return self.cleaned_data['HL_text_id'][5:]
