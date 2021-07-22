import re

import reversion
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from crum import get_current_request
from django.urls import reverse
from apis_core.helper_functions.ContentType import GetContentTypes


##############################################
#
#   Project classes
#
##############################################


class Project(models.Model):
    """Holds information on registered project.
    Id is used by the JavaScript function to target the right endpoints
    """

    name = models.CharField(max_length=255)  # name of the project registered
    user = models.ForeignKey(
        User, on_delete=models.CASCADE
    )  # foreignkey to the User who created the project
    description = models.TextField(blank=True, null=True)
    base_url = models.URLField(
        blank=True, null=True
    )  # optional base URL to restrict highlights to a base URL
    store_text = models.BooleanField(
        default=False
    )  # Whether to store the text in the tool or work with ids only.

    def __str__(self):
        return self.name

    class Meta:
        db_table = "highlighter_project"


class TextHigh(models.Model):
    """Holds unstructured text associated with
    one ore many entities/relations.
    """

    title = models.CharField(max_length=255, blank=True, null=True)
    text_choices = (("ft", "Full Text"), ("id", "Text ID"), ("cl", "Text Class"))
    text_type = models.CharField(max_length=3, choices=text_choices, default="cl")
    uri = models.URLField(
        blank=True, null=True
    )  # uri of vocab used to identify the text type
    text = models.TextField(blank=True, null=True)
    text_id = models.PositiveIntegerField(
        blank=True, null=True
    )  # UID to identify the text within the project. Allows to not upload the texts.
    text_class = models.CharField(max_length=255, blank=True, null=True)
    project = models.ForeignKey(
        Project, blank=True, null=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.title

    class Meta:
        db_table = "highlighter_texthigh"


class AnnotationProject(models.Model):
    """Every Project can have several Annotation Projects. Annotation Projects are used to track the precission etc.
    of automatic annotation tools.
    """

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    published = models.BooleanField(default=False)

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._loaded_values = dict(zip(field_names, values))
        return instance

    def save(self, *args, **kwargs):
        if hasattr(self, "_loaded_values"):
            if self.published != self._loaded_values["published"]:
                for ann in self.annotation_set.all():
                    ent = ann.entity_link
                    if ent is not None and ent.published != self.published:
                        ent.published = self.published
                        ent.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "highlighter_annotationproject"




@reversion.register()
class Annotation(models.Model):
    """Class storing highlights in full-texts"""

    class CustomGenericManager(models.Manager):

        def filter(self, *args, **kwargs):

            for key in kwargs.keys():
                if "entity_link_" in key:
                    raise Exception(
                        "'entity_link' is a custom filter work-around and can not handle django's "
                        "relation resolver. It's only possible to use 'entity_link' to filter for "
                        "exactly one related model instance! "
                        "(e.g. Annotation.objects.filter(entity_link=person))"
                    )

            if "entity_link" in kwargs:
                model_instance = kwargs.pop("entity_link")
                if model_instance is None:
                    kwargs["content_type"] = None
                    kwargs["object_id"] = None
                else:
                    kwargs["content_type"] = \
                        GetContentTypes.get_content_type_of_class_or_instance(model_class_or_instance=model_instance)
                    kwargs["object_id"] = model_instance.pk

            return super().filter(*args, **kwargs)

    set_highlighter = getattr(
        settings,
        "APIS_HIGHLIGHTER_ENTITIES",
        (
            "apis_entities.Person",
            "apis_entities.Institution",
            "apis_entities.Place",
            "apis_entities.Event",
            "apis_entities.Work",
            "apis_relations.PersonPerson",
            "apis_relations.PersonPlace",
            "apis_relations.PersonInstitution",
            "apis_relations.PersonEvent",
            "apis_relations.PersonWork",
            "apis_relations.InstitutionPlace",
            "apis_relations.InstitutionEvent",
            "apis_relations.InstitutionWork",
            "apis_relations.InstitutionInstitution",
            "apis_relations.PlaceEvent",
            "apis_relations.PlaceWork",
            "apis_relations.PlacePlace",
            "apis_relations.EventWork",
            "apis_relations.EventEvent",
            "apis_relations.WorkWork",
        ),
    )
    status_choices = (("del", "deleted"), ("ap", "approved"))
    start = models.PositiveIntegerField()  # number of string to start highlight
    end = models.PositiveIntegerField()  # number of string to end highlight
    content_type = models.ForeignKey(ContentType, related_name="gfk_from", on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    entity_link = GenericForeignKey("content_type", "object_id")
    objects = CustomGenericManager()
    entity_candidate = models.ManyToManyField("apis_metainfo.UriCandidate", blank=True)
    orig_string = models.CharField(
        max_length=255, blank=True, null=True
    )  # string originally highlighted
    text = models.ForeignKey("apis_metainfo.Text", on_delete=models.CASCADE)
    parent = models.ForeignKey(
        "self",
        related_name="parent_annotation",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )  # parent annotations are used to allow for a stacked design of the annotation project
    user_added = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.SET_NULL
    )  # changed from default=12
    annotation_project = models.ForeignKey(
        AnnotationProject, blank=True, null=True, on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=4, choices=status_choices, blank=True, null=True
    )

    def __str__(self):
        return "{}".format(self.pk)

    def trim_whitespaces(self, char):
        test = True
        while test and char < self.text_length:
            if self.text.text[char] == " ":
                test = True
                char += 1
            else:
                return char

    def annotation_hash(self, format_string="start_end_text_ent_entid"):
        """
        Function that returns a hash of the annotaion used to calculate inter-annotator agreement.

        :return:
        """
        matching = {"start": "start", "end": "end", "text": "text_id"}
        f_list = format_string.split("_")
        if "start" not in f_list or "end" not in f_list or "text" not in f_list:
            raise AttributeError(
                "Start, end and text must be present in the format_string parameter"
            )
        res = ""
        self.text_length = len(self.text.text)
        self.start = self.trim_whitespaces(self.start)
        self.end = self.trim_whitespaces(self.end)
        for f in f_list:
            if f in matching.keys():
                res += str(getattr(self, matching[f]))
            else:
                ent_link = self.entity_link
                if ent_link is not None:
                    cont_lst = str(
                        ContentType.objects.get_for_model(ent_link)
                    ).split()
                    if f == "ent":
                        res += "".join(cont_lst)
                    elif f == "entid":
                        for cont in cont_lst:
                            if hasattr(ent_link, "related_" + cont.strip()):
                                res += str(
                                    getattr(
                                        ent_link, "related_" + cont.strip() + "_id"
                                    )
                                )
                            elif hasattr(ent_link, "related_" + cont.strip() + "A"):
                                res += str(
                                    getattr(
                                        ent_link, "related_" + cont.strip() + "A_id"
                                    )
                                )
                            elif hasattr(ent_link, "related_" + cont.strip() + "B"):
                                res += str(
                                    getattr(
                                        ent_link, "related_" + cont.strip() + "B_id"
                                    )
                                )
                            res += "-"
                        res = res[:-1]
                    elif f == "rel":
                        res += str(getattr(ent_link, "relation_type_id"))
                else:
                    res += "NONE"


            res += "_"
        return res[:-1]

    def get_related_entity(self):
        return self.entity_link


    def get_html_markup(self, include_object=False):
        if self.entity_link is None:
            return None
        rel_entity = self.entity_link
        if hasattr(rel_entity, "relation_type"):
            entity_kind = str(rel_entity.relation_type.pk)
        elif hasattr(rel_entity, "kind"):
            entity_kind = str(rel_entity.kind.pk)
        else:
            entity_kind = str(0)
        entity_type = type(rel_entity).__name__
        entity_type_app = ContentType.objects.get(model=entity_type.lower()).app_label
        ent_lst_pk = []
        if self.user_added is not None:
            user_added = self.user_added.username[:2]
        else:
            user_added = "na"
        if entity_type_app.lower() == "apis_relations":
            for x in dir(rel_entity):
                c = re.match("related_\w+_id", x)
                if c:
                    ent_lst_pk.append(str(getattr(rel_entity, c.group(0))))
        start_span = """<mark class="highlight hl_text_{}" data-hl-type="simple" data-hl-start="{}"
            data-hl-end="{}" data-hl-text-id="{}" data-hl-ann-id="{}" data-entity-class="{}" data-entity-pk="{}"
            data-related-entity-pk="{}" data-entity-type="{}" data-user-added={}>""".format(
            entity_kind,
            self.start,
            self.end,
            self.text_id,
            self.pk,
            entity_type,
            rel_entity.pk,
            ",".join(ent_lst_pk),
            entity_type_app,
            user_added,
        )
        start_span = start_span.replace("\n", "")
        if include_object:
            request = get_current_request()
            if request is None:
                base = getattr(settings, "APIS_BASE_URI", "http://to_change.com")
                if base.endswith("/"):
                    base = base[:-1]
                url = f'{base}{reverse("apis:apis_api:{}-detail".format(entity_type.lower()), kwargs={"pk": rel_entity.pk},)}'
            else:
                url = request.build_absolute_uri(
                    reverse(
                        "apis:apis_api:{}-detail".format(entity_type.lower()),
                        kwargs={"pk": rel_entity.pk},
                    )
                )
            res_obj = {
                "id": self.id,
                "start": self.start,
                "end": self.end,
                "related_object": {
                    "id": rel_entity.id,
                    "url": url,
                    "type": entity_type,
                    "label": str(rel_entity),
                },
            }
            return start_span, res_obj
        return start_span

    class Meta:
        db_table = "highlighter_annotation"


##############################################
#
#   Configuration Classes
#
##############################################


class VocabularyAPI(models.Model):
    """Class storing the information of the endpoints of the vocabularies."""

    method_lst = (("l", "local"), ("o", "open skos"))
    name = models.CharField(max_length=255, null=True, blank=True)
    api_endpoint = models.CharField(max_length=255, null=True, blank=True)
    method = models.CharField(max_length=2, choices=method_lst, default="l")

    def __str__(self):
        return self.name

    class Meta:
        db_table = "highlighter_vocabularyapi"


class MenuEntry(models.Model):
    """Class that defines the menu structure of the context menu"""

    choices_kind = (
        ("txt", "Text field"),
        ("frm", "Form"),
        ("m", "menu entry"),
        ("fn", "Javascript function"),
    )
    kind = models.CharField(max_length=4, choices=choices_kind, default="txt")
    name = models.CharField(
        max_length=255, null=True, blank=True
    )  # Charfield used when txt is as type of entry specified
    api = models.ForeignKey(
        VocabularyAPI, blank=True, null=True, on_delete=models.SET_NULL
    )  # Foreignkey used to link the API entry in case api is set as kind
    parent = models.ForeignKey(
        "self",
        related_name="parent_menuEntry",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    project = models.ForeignKey(
        Project, null=True, blank=True, on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "highlighter_menuentry"


#######################################################################
#
# DL-Classes
#
#######################################################################


class ActiveLearningProject(models.Model):
    """Used to store active learning project settings."""

    choices = ""
    name = models.CharField(max_length=255)
    sampling_strategy = models.CharField(max_length=4, choices=choices)
    rebuild = models.IntegerField()
    collection = models
    log_dir = models.CharField(max_length=255)

    class Meta:
        db_table = "highlighter_activelearningproject"
