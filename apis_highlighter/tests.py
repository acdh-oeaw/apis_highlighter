from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from apis_core.apis_metainfo.models import Text
from apis_core.apis_entities.models import Person, Institution, Event
from django.contrib.auth.models import User
from .models import Annotation
from rest_framework import status
from random import randint


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

    def test_hard(self):

        def randomize_and_compare(text_object, mutation_iteration):

            class Fragment():

                def __init__(self, text=None, is_annotated=None):
                    self.text = text
                    self.is_annotated = is_annotated


            def create_fragment_list(text_str, anns_ordered):
                # create list of subtext, differentiating between annotated and non-annotated fragments

                s = 0
                e = 0
                ann_current = None
                fragment_list = []
                while e < len(text_str) - 1:
                    if ann_current is None:
                        if len(anns_ordered) > 0:
                            ann_current = anns_ordered[0]
                            del anns_ordered[0]
                            e = ann_current.start
                            fragment_list.append(
                                Fragment(
                                    text=text_str[s:e],
                                    is_annotated=False,
                                )
                            )
                            s = ann_current.start
                        else:
                            e = len(text_str)
                            fragment_list.append(
                                Fragment(
                                    text=text_str[s:e],
                                    is_annotated=False,
                                )
                            )
                    else:
                        if len(anns_ordered) > 0:
                            ann_next = anns_ordered[0]
                            if ann_current.end < ann_next.start:
                                e = ann_current.end
                                fragment_list.append(
                                    Fragment(
                                        text=text_str[s:e],
                                        is_annotated=True,
                                    )
                                )
                                s = ann_current.end
                                ann_current = None
                            else:
                                ann_current = ann_next
                                del anns_ordered[0]
                        else:
                            e = ann_current.end
                            fragment_list.append(
                                Fragment(
                                    text=text_str[s:e],
                                    is_annotated=True,
                                )
                            )
                            s = ann_current.end
                            ann_current = None

                return fragment_list


            def randomize_texts(fragment_list, mutation_iteration):

                def get_random_pos(s):

                    return randint(0, len(s) - 1)

                def chance_50():

                    if randint(0,1) == 1:
                        return True
                    else:
                        return False

                def chance_66():

                    if randint(0, 2) < 2:
                        return True
                    else:
                        return False

                def randomize_string(t):

                    if chance_50(): # 50% chance for randomizing this text
                        s = get_random_pos(t) # random start index for subtext
                        e = get_random_pos(t) # random end index for subtext
                        if s > e:
                            tmp = s
                            s = e
                            e = tmp
                        diff = e - s
                        s += round(diff / 4) # minimizing the distance between subtext-indices to make subtext smaller
                        e -= round(diff / 4)
                        if chance_66(): # 66% chance for adding subtext
                            if chance_50(): # 50% chance for adding subtext to end
                                t = t + t[s:e]
                            else: # 50% chance for adding subtext to front
                                t = t[s:e] + t
                        else: # 33% chance for removing subtext
                            t = t[:s] + t[e:]
                        if chance_50():
                            i = get_random_pos(t)
                            t = t[:i] + "\n" + t[i:]

                    return t

                for i in range(mutation_iteration):
                    for fragment in fragment_list:
                        if not fragment.is_annotated:
                            fragment.text = randomize_string(fragment.text)

                return "".join([f.text for f in fragment_list])

            def main(text_object, mutation_iteration):

                anns_ordered = list(text_object.annotation_set.all().order_by("start"))
                text_original = text_object.text
                anns_to_compare = {}
                for ann in anns_ordered:
                    anns_to_compare[ann.pk] = {
                        "old": text_original[ann.start:ann.end],
                        "new": None,
                        "correct": None
                    }
                fragment_list = create_fragment_list(text_original, anns_ordered)
                text_object.text = randomize_texts(fragment_list, mutation_iteration)
                text_object.save()
                for ann in text_object.annotation_set.all():
                    anns_to_compare[ann.pk]["new"] = text_object.text[ann.start:ann.end]
                    anns_to_compare[ann.pk]["correct"] = anns_to_compare[ann.pk]["old"] == anns_to_compare[ann.pk]["new"]
                for k in anns_to_compare.keys():
                    d = anns_to_compare[k]
                    if d["correct"] == True:
                        print(f"id: {k} - correct")
                    elif d["correct"] == False:
                        print(f"id: {k} - ERROR: Wrong text")
                        is_all_good = False
                    elif d["correct"] is None:
                        print(f"id: {k} - ERROR: Annotation was deleted")
                        is_all_good = False

            main(text_object, mutation_iteration)

        print("---------------------------------------------------------")
        print("Starting random mutation of non-annotated text fragments")

        for mutation_iteration in range(0, 6):

            text_object = Text.objects.create(
                text=r"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aliquam gravida dui eget erat laoreet, a porttitor nisl fermentum. Sed quis metus sed risus tincidunt blandit. Aliquam eu ultricies ipsum. Sed quis vulputate libero, eget hendrerit ligula. Suspendisse sed diam purus. Ut pretium mattis nisl, nec posuere urna porta eu. Donec sit amet risus leo. Suspendisse risus sapien, tristique eget pulvinar condimentum, luctus eu dui. Maecenas maximus vulputate elit at suscipit. Nunc ac suscipit nisi, ac pretium eros. Mauris eget aliquam metus. Morbi ut euismod dolor, vitae ultrices orci. Maecenas vulputate placerat libero eu porta. Morbi rutrum ex a ipsum rutrum aliquet. Donec quis neque efficitur, auctor enim sed, sagittis lorem. Aliquam dictum lacus a tempus pulvinar. \nProin in neque imperdiet tellus iaculis venenatis fermentum in sem. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Curabitur tincidunt a elit quis ultrices. Nullam pulvinar a ligula quis blandit. In nec lacus eu risus imperdiet pharetra. Proin vel elit at ipsum gravida faucibus non sit amet lectus. Duis pulvinar vestibulum interdum. Nullam ullamcorper risus sit amet nisi elementum mollis. Aenean non enim libero. \nInteger condimentum dolor sed dolor pulvinar, sed lacinia nisi tempor. Quisque turpis lorem, convallis ac egestas a, condimentum a enim. Praesent eget mauris a quam fringilla porta eu eget urna. Integer tristique urna leo, in auctor ante faucibus eget. Aliquam erat volutpat. Nunc turpis ex, hendrerit sed elit dignissim, rhoncus consectetur tortor. Praesent semper eros et eros tristique scelerisque. Nulla erat enim, aliquam vitae commodo vel, vehicula eu justo. Sed a venenatis nulla, vitae bibendum risus. Proin sed libero tincidunt mauris varius volutpat in at lectus. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Etiam vel lacus ut justo malesuada pharetra vitae in tellus. Donec ullamcorper sit amet ipsum in consequat. Mauris a ex cursus magna placerat convallis. Nam a lobortis ipsum. Nunc a vehicula mauris. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aliquam gravida dui eget erat laoreet, a porttitor nisl fermentum. Sed quis metus sed risus tincidunt blandit. Aliquam eu ultricies ipsum. Sed quis vulputate libero, eget hendrerit ligula. Suspendisse sed diam purus. Ut pretium mattis nisl, nec posuere urna porta eu. Donec sit amet risus leo. Suspendisse risus sapien, tristique eget pulvinar condimentum, luctus eu dui. Maecenas maximus vulputate elit at suscipit. Nunc ac suscipit nisi, ac pretium eros. Mauris eget aliquam metus. Morbi ut euismod dolor, vitae ultrices orci. Maecenas vulputate placerat libero eu porta. Morbi rutrum ex a ipsum rutrum aliquet. Donec quis neque efficitur, auctor enim sed, sagittis lorem. Aliquam dictum lacus a tempus pulvinar. \nProin in neque imperdiet tellus iaculis venenatis fermentum in sem. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Curabitur tincidunt a elit quis ultrices. Nullam pulvinar a ligula quis blandit. In nec lacus eu risus imperdiet pharetra. Proin vel elit at ipsum gravida faucibus non sit amet lectus. Duis pulvinar vestibulum interdum. Nullam ullamcorper risus sit amet nisi elementum mollis. Aenean non enim libero. \nInteger condimentum dolor sed dolor pulvinar, sed lacinia nisi tempor. Quisque turpis lorem, convallis ac egestas a, condimentum a enim. Praesent eget mauris a quam fringilla porta eu eget urna. Integer tristique urna leo, in auctor ante faucibus eget. Aliquam erat volutpat. Nunc turpis ex, hendrerit sed elit dignissim, rhoncus consectetur tortor. Praesent semper eros et eros tristique scelerisque. Nulla erat enim, aliquam vitae commodo vel, vehicula eu justo. Sed a venenatis nulla, vitae bibendum risus. Proin sed libero tincidunt mauris varius volutpat in at lectus. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Etiam vel lacus ut justo malesuada pharetra vitae in tellus. Donec ullamcorper sit amet ipsum in consequat. Mauris a ex cursus magna placerat convallis. Nam a lobortis ipsum. Nunc a vehicula mauris."
            )
            Annotation.objects.create(text=text_object, start=981, end=990)
            Annotation.objects.create(text=text_object, start=2575, end=2583)
            Annotation.objects.create(text=text_object, start=105, end=132)
            Annotation.objects.create(text=text_object, start=673, end=703)
            Annotation.objects.create(text=text_object, start=715, end=780)
            Annotation.objects.create(text=text_object, start=1297, end=1368)
            Annotation.objects.create(text=text_object, start=1829, end=1875)
            Annotation.objects.create(text=text_object, start=1987, end=2046)
            Annotation.objects.create(text=text_object, start=2257, end=2324)
            Annotation.objects.create(text=text_object, start=2382, end=2388)
            Annotation.objects.create(text=text_object, start=2392, end=2459)
            Annotation.objects.create(text=text_object, start=2748, end=2777)
            Annotation.objects.create(text=text_object, start=2815, end=2832)
            Annotation.objects.create(text=text_object, start=2845, end=2850)

            print(f"starting mutation iteration: {mutation_iteration}")

            randomize_and_compare(text_object, mutation_iteration)
