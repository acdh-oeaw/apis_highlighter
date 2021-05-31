from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from apis_core.apis_metainfo.models import Text
from apis_core.apis_entities.models import Person, Institution, Event
from django.contrib.auth.models import User
from .models import Annotation
from rest_framework import status


class HighlighterAPITestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        user = User.objects.create_user(username="lauren", password="pas_1234$")
        token = Token.objects.create(user=user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        cls.c = client
        txt = "Franz fuhr mit dem Rad nach Wien."
        start = 6
        end = 10
        start_1 = 19
        end_1 = 22
        start_2 = 28
        end_2 = 32
        print(txt[start:end])
        cls.text = Text.objects.create(text=txt)
        cls.text_original = txt
        cls.annotation = Annotation.objects.create(text=cls.text, start=start, end=end)
        cls.annotation_2 = Annotation.objects.create(
            text=cls.text, start=start_1, end=end_1
        )
        cls.annotation_3 = Annotation.objects.create(
            text=cls.text, start=start_2, end=end_2
        )
        pers = Person.objects.first()
        cls.annotation.entity_link.add(pers)
        inst = Institution.objects.first()
        cls.annotation_2.entity_link.add(inst)
        ev = Event.objects.first()
        cls.annotation_3.entity_link.add(ev)
        print(cls.annotation)

    def test_get(self):
        url = (
            reverse(f"apis:apis_core:text-detail", kwargs={"pk": self.text.pk})
            + "?format=json&highlight"
        )
        res = self.c.get(url)
        print(res)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        elements = res.json()
        if ">fuhr</mark>" not in elements["text"]:
            raise ValueError("Highlight not correct")
        print(self.annotation.start, self.annotation.end, self.text_original)
        self.assertEqual(
            self.text_original[self.annotation.start : self.annotation.end], "fuhr"
        )
        self.assertEqual(
            self.text_original[self.annotation_2.start : self.annotation_2.end], "Rad"
        )
        self.assertEqual(
            self.text_original[self.annotation_3.start : self.annotation_3.end], "Wien"
        )
        print(elements)

    def test_add_newlines(self):
        txt = "Franz\n fuhr mit\n\n dem Rad nach\n Wien."
        self.text.text = txt
        self.text.save()
        for an in Annotation.objects.filter(text=self.text):
            if self.text.text[an.start:an.end] not in ["fuhr", "Rad", "Wien"]:
                print(f"value pure annotation: {self.text.text[an.start:an.end]}")
                raise ValueError("Annotation not correctly moved")
            else:
                print(f"moved annotation: {self.text.text[an.start:an.end]}")

        url = (
            reverse(f"apis:apis_core:text-detail", kwargs={"pk": self.text.pk})
            + "?format=json&highlight"
        )
        res = self.c.get(url)
        print(res)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        elements = res.json()
        print(f"text section of return: {elements}")
        if ">fuhr</mark>" not in elements["text"]:
            raise ValueError("Highlight not correct")
        if ">Rad</mark>" not in elements["text"]:
            raise ValueError("second Highlight not correct")
        if ">Wien</mark>" not in elements["text"]:
            raise ValueError("third Highlight not correct")
