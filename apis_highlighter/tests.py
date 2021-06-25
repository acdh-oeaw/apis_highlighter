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
        cls.annotation.entity_link = pers
        cls.annotation.save()
        inst = Institution.objects.first()
        cls.annotation_2.entity_link = inst
        cls.annotation_2.save()
        ev = Event.objects.first()
        cls.annotation_3.entity_link = ev
        cls.annotation_3.save()
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

    def test_randomized(self):

        def randomize_and_compare(text_object, mutation_iteration):

            class Fragment():

                def __init__(self, text, is_annotated, ann_data_dict):
                    self.text = text
                    self.is_annotated = is_annotated
                    self.ann_data_dict = ann_data_dict


            def create_fragment_list(text_str, anns_ordered):
                # create list of subtext, differentiating between annotated and non-annotated fragments

                s = 0
                e = 0
                ann_current = None
                fragment_list = []
                while e < len(text_str) - 1:

                    if ann_current is None:

                        if len(anns_ordered) > 0:

                            ann_next = anns_ordered[0]
                            e = ann_next.start
                            if e - s > 0:
                                fragment_list.append(
                                    Fragment(
                                        text=text_str[s:e],
                                        is_annotated=False,
                                        ann_data_dict=None,
                                    )
                                )
                            ann_current = ann_next
                            del anns_ordered[0]
                            s = ann_current.start

                        else:

                            e = len(text_str)
                            if e - s > 0:
                                fragment_list.append(
                                    Fragment(
                                        text=text_str[s:e],
                                        is_annotated=False,
                                        ann_data_dict=None,
                                    )
                                )

                    else:

                        e = ann_current.end
                        fragment_list.append(
                            Fragment(
                                text=text_str[s:e],
                                is_annotated=True,
                                ann_data_dict={
                                    "id": ann_current.pk,
                                    "start": ann_current.start,
                                    "end": ann_current.end
                                },
                            )
                        )

                        if len(anns_ordered) > 0:

                            ann_next = anns_ordered[0]

                            if e < ann_next.start:
                                ann_current = None
                                s = e
                            else:
                                ann_current = ann_next
                                del anns_ordered[0]
                                s = ann_current.start

                        else:

                            s = ann_current.end
                            ann_current = None

                return fragment_list


            def randomize_texts(fragment_list, mutation_iteration):

                def get_random_pos(s):

                    return randint(0, len(s) - 1)

                def chance_50():

                    return randint(0, 1) == 1

                def chance_66():

                    return randint(0, 2) < 2

                def randomize_string(t):

                    len_before = len(t)

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

                    len_diff = len(t) - len_before

                    return (t, len_diff)

                for i in range(mutation_iteration):

                    for j in range(len(fragment_list)):

                        fragment = fragment_list[j]
                        if not fragment.is_annotated:
                            fragment.text, len_diff = randomize_string(fragment.text)

                            if j + 1 < len(fragment_list) and len_diff != 0:

                                for fragment_next in fragment_list[j+1:]:

                                    if fragment_next.is_annotated:

                                        ann_data_dict = fragment_next.ann_data_dict

                                        ann_data_dict["start"] = ann_data_dict["start"] + len_diff
                                        ann_data_dict["end"] = ann_data_dict["end"] + len_diff

                text_new = ""

                for j in range(len(fragment_list)):

                    fragment = fragment_list[j]

                    if not fragment.is_annotated:

                        text_new += fragment.text

                    else:

                        if j + 1 < len(fragment_list):

                            fragment_next = fragment_list[j+1]

                            if fragment_next.is_annotated:

                                if fragment.ann_data_dict["end"] < fragment_next.ann_data_dict["start"]:

                                    text_new += fragment.text

                                else:

                                    len_till_start = fragment_next.ann_data_dict["start"] - fragment.ann_data_dict["start"]
                                    text_new += fragment.text[:len_till_start]

                            else:

                                text_new += fragment.text

                return (fragment_list, text_new)

            def main(text_object, mutation_iteration):

                anns_ordered = list(text_object.annotation_set.all().order_by("start"))
                text_original = text_object.text
                anns_to_compare = {}
                for ann in anns_ordered:
                    anns_to_compare[ann.pk] = {
                        "text_old": text_original[ann.start:ann.end],
                        "start_old": ann.start,
                        "end_old": ann.end,
                        "text_new": None,
                        "start_new": None,
                        "end_new": None,
                        "correct": None,
                    }
                fragment_list = create_fragment_list(text_original, anns_ordered)


                fragment_list, text_new = randomize_texts(fragment_list, mutation_iteration)

                for fragment in fragment_list:

                    if fragment.is_annotated:

                        ann_data_dict = fragment.ann_data_dict

                        ann_compare_dict = anns_to_compare[ann_data_dict["id"]]
                        ann_compare_dict["start_new"] = ann_data_dict["start"]
                        ann_compare_dict["end_new"] = ann_data_dict["end"]

                text_object.text = text_new
                text_object.save()

                for ann in text_object.annotation_set.all():

                    ann_compare_dict = anns_to_compare[ann.pk]

                    ann_compare_dict["text_new"] = text_object.text[ann.start:ann.end]
                    ann_compare_dict["correct"] = (
                        ann_compare_dict["text_old"] == ann_compare_dict["text_new"]
                        and ann_compare_dict["start_new"] == ann.start
                        and ann_compare_dict["end_new"] == ann.end
                        and text_new[ann_compare_dict["start_new"]:ann_compare_dict["end_new"]] == ann_compare_dict["text_old"]
                    )

                for k in anns_to_compare.keys():
                    d = anns_to_compare[k]
                    if d["correct"] == True:
                        print(f"id: {k} - correct")
                    elif d["correct"] == False:
                        print(f"id: {k} - ERROR: Wrong text")
                    elif d["correct"] is None:
                        print(f"id: {k} - ERROR: Annotation was deleted")

            main(text_object, mutation_iteration)

        print("---------------------------------------------------------")
        print("Starting random mutation of non-annotated text fragments")

        for mutation_iteration in range(0, 11):

            def get_rand_start_end(t):

                rand_start = randint(0, len(t))
                rand_end = rand_start + randint(10, 40)
                if rand_end >= len(t):
                    rand_end = len(t) - 1

                return (rand_start, rand_end)


            text_raw = "\n1:1 In the beginning God created the heaven and the earth.\n\n1:2 And the earth was without form, and void; and darkness was upon\nthe face of the deep. And the Spirit of God moved upon the face of the\nwaters.\n\n1:3 And God said, Let there be light: and there was light.\n\n1:4 And God saw the light, that it was good: and God divided the light\nfrom the darkness.\n\n1:5 And God called the light Day, and the darkness he called Night.\nAnd the evening and the morning were the first day.\n\n1:6 And God said, Let there be a firmament in the midst of the waters,\nand let it divide the waters from the waters.\n\n1:7 And God made the firmament, and divided the waters which were\nunder the firmament from the waters which were above the firmament:\nand it was so.\n\n1:8 And God called the firmament Heaven. And the evening and the\nmorning were the second day.\n\n1:9 And God said, Let the waters under the heaven be gathered together\nunto one place, and let the dry land appear: and it was so.\n\n1:10 And God called the dry land Earth; and the gathering together of\nthe waters called he Seas: and God saw that it was good.\n\n1:11 And God said, Let the earth bring forth grass, the herb yielding\nseed, and the fruit tree yielding fruit after his kind, whose seed is\nin itself, upon the earth: and it was so.\n\n1:12 And the earth brought forth grass, and herb yielding seed after\nhis kind, and the tree yielding fruit, whose seed was in itself, after\nhis kind: and God saw that it was good.\n\n1:13 And the evening and the morning were the third day.\n\n1:14 And God said, Let there be lights in the firmament of the heaven\nto divide the day from the night; and let them be for signs, and for\nseasons, and for days, and years: 1:15 And let them be for lights in\nthe firmament of the heaven to give light upon the earth: and it was\nso.\n\n1:16 And God made two great lights; the greater light to rule the day,\nand the lesser light to rule the night: he made the stars also.\n\n1:17 And God set them in the firmament of the heaven to give light\nupon the earth, 1:18 And to rule over the day and over the night, and\nto divide the light from the darkness: and God saw that it was good.\n\n1:19 And the evening and the morning were the fourth day.\n\n1:20 And God said, Let the waters bring forth abundantly the moving\ncreature that hath life, and fowl that may fly above the earth in the\nopen firmament of heaven.\n\n1:21 And God created great whales, and every living creature that\nmoveth, which the waters brought forth abundantly, after their kind,\nand every winged fowl after his kind: and God saw that it was good.\n\n1:22 And God blessed them, saying, Be fruitful, and multiply, and fill\nthe waters in the seas, and let fowl multiply in the earth.\n\n1:23 And the evening and the morning were the fifth day.\n\n1:24 And God said, Let the earth bring forth the living creature after\nhis kind, cattle, and creeping thing, and beast of the earth after his\nkind: and it was so.\n\n1:25 And God made the beast of the earth after his kind, and cattle\nafter their kind, and every thing that creepeth upon the earth after\nhis kind: and God saw that it was good.\n\n1:26 And God said, Let us make man in our image, after our likeness:\nand let them have dominion over the fish of the sea, and over the fowl\nof the air, and over the cattle, and over all the earth, and over\nevery creeping thing that creepeth upon the earth.\n\n1:27 So God created man in his own image, in the image of God created\nhe him; male and female created he them.\n\n1:28 And God blessed them, and God said unto them, Be fruitful, and\nmultiply, and replenish the earth, and subdue it: and have dominion\nover the fish of the sea, and over the fowl of the air, and over every\nliving thing that moveth upon the earth.\n\n1:29 And God said, Behold, I have given you every herb bearing seed,\nwhich is upon the face of all the earth, and every tree, in the which\nis the fruit of a tree yielding seed; to you it shall be for meat.\n\n1:30 And to every beast of the earth, and to every fowl of the air,\nand to every thing that creepeth upon the earth, wherein there is\nlife, I have given every green herb for meat: and it was so.\n\n1:31 And God saw every thing that he had made, and, behold, it was\nvery good. And the evening and the morning were the sixth day.\n\n2:1 Thus the heavens and the earth were finished, and all the host of\nthem.\n\n2:2 And on the seventh day God ended his work which he had made; and\nhe rested on the seventh day from all his work which he had made.\n\n2:3 And God blessed the seventh day, and sanctified it: because that\nin it he had rested from all his work which God created and made.\n\n2:4 These are the generations of the heavens and of the earth when\nthey were created, in the day that the LORD God made the earth and the\nheavens, 2:5 And every plant of the field before it was in the earth,\nand every herb of the field before it grew: for the LORD God had not\ncaused it to rain upon the earth, and there was not a man to till the\nground.\n\n2:6 But there went up a mist from the earth, and watered the whole\nface of the ground.\n\n2:7 And the LORD God formed man of the dust of the ground, and\nbreathed into his nostrils the breath of life; and man became a living\nsoul.\n\n2:8 And the LORD God planted a garden eastward in Eden; and there he\nput the man whom he had formed.\n\n2:9 And out of the ground made the LORD God to grow every tree that is\npleasant to the sight, and good for food; the tree of life also in the\nmidst of the garden, and the tree of knowledge of good and evil.\n\n2:10 And a river went out of Eden to water the garden; and from thence\nit was parted, and became into four heads.\n\n2:11 The name of the first is Pison: that is it which compasseth the\nwhole land of Havilah, where there is gold; 2:12 And the gold of that\nland is good: there is bdellium and the onyx stone.\n\n2:13 And the name of the second river is Gihon: the same is it that\ncompasseth the whole land of Ethiopia.\n\n2:14 And the name of the third river is Hiddekel: that is it which\ngoeth toward the east of Assyria. And the fourth river is Euphrates.\n\n2:15 And the LORD God took the man, and put him into the garden of\nEden to dress it and to keep it.\n\n2:16 And the LORD God commanded the man, saying, Of every tree of the\ngarden thou mayest freely eat: 2:17 But of the tree of the knowledge\nof good and evil, thou shalt not eat of it: for in the day that thou\neatest thereof thou shalt surely die.\n\n2:18 And the LORD God said, It is not good that the man should be\nalone; I will make him an help meet for him.\n\n2:19 And out of the ground the LORD God formed every beast of the\nfield, and every fowl of the air; and brought them unto Adam to see\nwhat he would call them: and whatsoever Adam called every living\ncreature, that was the name thereof.\n\n2:20 And Adam gave names to all cattle, and to the fowl of the air,\nand to every beast of the field; but for Adam there was not found an\nhelp meet for him.\n\n2:21 And the LORD God caused a deep sleep to fall upon Adam, and he\nslept: and he took one of his ribs, and closed up the flesh instead\nthereof; 2:22 And the rib, which the LORD God had taken from man, made\nhe a woman, and brought her unto the man.\n\n2:23 And Adam said, This is now bone of my bones, and flesh of my\nflesh: she shall be called Woman, because she was taken out of Man.\n\n2:24 Therefore shall a man leave his father and his mother, and shall\ncleave unto his wife: and they shall be one flesh.\n\n2:25 And they were both naked, the man and his wife, and were not\nashamed.\n\n3:1 Now the serpent was more subtil than any beast of the field which\nthe LORD God had made. And he said unto the woman, Yea, hath God said,\nYe shall not eat of every tree of the garden?  3:2 And the woman said\nunto the serpent, We may eat of the fruit of the trees of the garden:\n3:3 But of the fruit of the tree which is in the midst of the garden,\nGod hath said, Ye shall not eat of it, neither shall ye touch it, lest\nye die.\n\n3:4 And the serpent said unto the woman, Ye shall not surely die: 3:5\nFor God doth know that in the day ye eat thereof, then your eyes shall\nbe opened, and ye shall be as gods, knowing good and evil.\n\n3:6 And when the woman saw that the tree was good for food, and that\nit was pleasant to the eyes, and a tree to be desired to make one\nwise, she took of the fruit thereof, and did eat, and gave also unto\nher husband with her; and he did eat.\n\n3:7 And the eyes of them both were opened, and they knew that they\nwere naked; and they sewed fig leaves together, and made themselves\naprons.\n\n3:8 And they heard the voice of the LORD God walking in the garden in\nthe cool of the day: and Adam and his wife hid themselves from the\npresence of the LORD God amongst the trees of the garden.\n\n3:9 And the LORD God called unto Adam, and said unto him, Where art\nthou?  3:10 And he said, I heard thy voice in the garden, and I was\nafraid, because I was naked; and I hid myself.\n\n3:11 And he said, Who told thee that thou wast naked? Hast thou eaten\nof the tree, whereof I commanded thee that thou shouldest not eat?\n3:12 And the man said, The woman whom thou gavest to be with me, she\ngave me of the tree, and I did eat.\n\n3:13 And the LORD God said unto the woman, What is this that thou hast\ndone? And the woman said, The serpent beguiled me, and I did eat.\n\n3:14 And the LORD God said unto the serpent, Because thou hast done\nthis, thou art cursed above all cattle, and above every beast of the\nfield; upon thy belly shalt thou go, and dust shalt thou eat all the\ndays of thy life: 3:15 And I will put enmity between thee and the\nwoman, and between thy seed and her seed; it shall bruise thy head,\nand thou shalt bruise his heel.\n\n3:16 Unto the woman he said, I will greatly multiply thy sorrow and\nthy conception; in sorrow thou shalt bring forth children; and thy\ndesire shall be to thy husband, and he shall rule over thee.\n\n3:17 And unto Adam he said, Because thou hast hearkened unto the voice\nof thy wife, and hast eaten of the tree, of which I commanded thee,\nsaying, Thou shalt not eat of it: cursed is the ground for thy sake;\nin sorrow shalt thou eat of it all the days of thy life; 3:18 Thorns\nalso and thistles shall it bring forth to thee; and thou shalt eat the\nherb of the field; 3:19 In the sweat of thy face shalt thou eat bread,\ntill thou return unto the ground; for out of it wast thou taken: for\ndust thou art, and unto dust shalt thou return.\n\n3:20 And Adam called his wife's name Eve; because she was the mother\nof all living.\n\n3:21 Unto Adam also and to his wife did the LORD God make coats of\nskins, and clothed them.\n\n3:22 And the LORD God said, Behold, the man is become as one of us, to\nknow good and evil: and now, lest he put forth his hand, and take also\nof the tree of life, and eat, and live for ever: 3:23 Therefore the\nLORD God sent him forth from the garden of Eden, to till the ground\nfrom whence he was taken.\n\n3:24 So he drove out the man; and he placed at the east of the garden\nof Eden Cherubims, and a flaming sword which turned every way, to keep\nthe way of the tree of life.\n\n4:1 And Adam knew Eve his wife; and she conceived, and bare Cain, and\nsaid, I have gotten a man from the LORD.\n\n4:2 And she again bare his brother Abel. And Abel was a keeper of\nsheep, but Cain was a tiller of the ground.\n\n4:3 And in process of time it came to pass, that Cain brought of the\nfruit of the ground an offering unto the LORD.\n\n4:4 And Abel, he also brought of the firstlings of his flock and of\nthe fat thereof. And the LORD had respect unto Abel and to his\noffering: 4:5 But unto Cain and to his offering he had not respect.\nAnd Cain was very wroth, and his countenance fell.\n\n4:6 And the LORD said unto Cain, Why art thou wroth? and why is thy\ncountenance fallen?  4:7 If thou doest well, shalt thou not be\naccepted? and if thou doest not well, sin lieth at the door. And unto\nthee shall be his desire, and thou shalt rule over him.\n\n4:8 And Cain talked with Abel his brother: and it came to pass, when\nthey were in the field, that Cain rose up against Abel his brother,\nand slew him.\n\n4:9 And the LORD said unto Cain, Where is Abel thy brother? And he\nsaid, I know not: Am I my brother's keeper?  4:10 And he said, What\nhast thou done? the voice of thy brother's blood crieth unto me from\nthe ground.\n\n4:11 And now art thou cursed from the earth, which hath opened her\nmouth to receive thy brother's blood from thy hand; 4:12 When thou\ntillest the ground, it shall not henceforth yield unto thee her\nstrength; a fugitive and a vagabond shalt thou be in the earth.\n\n4:13 And Cain said unto the LORD, My punishment is greater than I can\nbear.\n\n4:14 Behold, thou hast driven me out this day from the face of the\nearth; and from thy face shall I be hid; and I shall be a fugitive and\na vagabond in the earth; and it shall come to pass, that every one\nthat findeth me shall slay me.\n\n4:15 And the LORD said unto him, Therefore whosoever slayeth Cain,\nvengeance shall be taken on him sevenfold. And the LORD set a mark\nupon Cain, lest any finding him should kill him.\n\n4:16 And Cain went out from the presence of the LORD, and dwelt in the\nland of Nod, on the east of Eden.\n\n4:17 And Cain knew his wife; and she conceived, and bare Enoch: and he\nbuilded a city, and called the name of the city, after the name of his\nson, Enoch.\n\n4:18 And unto Enoch was born Irad: and Irad begat Mehujael: and\nMehujael begat Methusael: and Methusael begat Lamech.\n\n4:19 And Lamech took unto him two wives: the name of the one was Adah,\nand the name of the other Zillah.\n\n4:20 And Adah bare Jabal: he was the father of such as dwell in tents,\nand of such as have cattle.\n\n4:21 And his brother's name was Jubal: he was the father of all such\nas handle the harp and organ.\n\n4:22 And Zillah, she also bare Tubalcain, an instructer of every\nartificer in brass and iron: and the sister of Tubalcain was Naamah.\n\n4:23 And Lamech said unto his wives, Adah and Zillah, Hear my voice;\nye wives of Lamech, hearken unto my speech: for I have slain a man to\nmy wounding, and a young man to my hurt.\n\n4:24 If Cain shall be avenged sevenfold, truly Lamech seventy and\nsevenfold.\n\n4:25 And Adam knew his wife again; and she bare a son, and called his\nname Seth: For God, said she, hath appointed me another seed instead\nof Abel, whom Cain slew.\n\n4:26 And to Seth, to him also there was born a son; and he called his\nname Enos: then began men to call upon the name of the LORD.\n\n5:1 This is the book of the generations of Adam. In the day that God\ncreated man, in the likeness of God made he him; 5:2 Male and female\ncreated he them; and blessed them, and called their name Adam, in the\nday when they were created.\n\n5:3 And Adam lived an hundred and thirty years, and begat a son in his\nown likeness, and after his image; and called his name Seth: 5:4 And\nthe days of Adam after he had begotten Seth were eight hundred years:\nand he begat sons and daughters: 5:5 And all the days that Adam lived\nwere nine hundred and thirty years: and he died.\n\n5:6 And Seth lived an hundred and five years, and begat Enos: 5:7 And\nSeth lived after he begat Enos eight hundred and seven years, and\nbegat sons and daughters: 5:8 And all the days of Seth were nine\nhundred and twelve years: and he died.\n\n5:9 And Enos lived ninety years, and begat Cainan: 5:10 And Enos lived\nafter he begat Cainan eight hundred and fifteen years, and begat sons\nand daughters: 5:11 And all the days of Enos were nine hundred and\nfive years: and he died.\n\n5:12 And Cainan lived seventy years and begat Mahalaleel: 5:13 And\nCainan lived after he begat Mahalaleel eight hundred and forty years,\nand begat sons and daughters: 5:14 And all the days of Cainan were\nnine hundred and ten years: and he died.\n\n5:15 And Mahalaleel lived sixty and five years, and begat Jared: 5:16\nAnd Mahalaleel lived after he begat Jared eight hundred and thirty\nyears, and begat sons and daughters: 5:17 And all the days of\nMahalaleel were eight hundred ninety and five years: and he died.\n\n5:18 And Jared lived an hundred sixty and two years, and he begat\nEnoch: 5:19 And Jared lived after he begat Enoch eight hundred years,\nand begat sons and daughters: 5:20 And all the days of Jared were nine\nhundred sixty and two years: and he died.\n\n5:21 And Enoch lived sixty and five years, and begat Methuselah: 5:22\nAnd Enoch walked with God after he begat Methuselah three hundred\nyears, and begat sons and daughters: 5:23 And all the days of Enoch\nwere three hundred sixty and five years: 5:24 And Enoch walked with\nGod: and he was not; for God took him.\n\n5:25 And Methuselah lived an hundred eighty and seven years, and begat\nLamech.\n\n5:26 And Methuselah lived after he begat Lamech seven hundred eighty\nand two years, and begat sons and daughters: 5:27 And all the days of\nMethuselah were nine hundred sixty and nine years: and he died.\n\n5:28 And Lamech lived an hundred eighty and two years, and begat a\nson: 5:29 And he called his name Noah, saying, This same shall comfort\nus concerning our work and toil of our hands, because of the ground\nwhich the LORD hath cursed.\n\n5:30 And Lamech lived after he begat Noah five hundred ninety and five\nyears, and begat sons and daughters: 5:31 And all the days of Lamech\nwere seven hundred seventy and seven years: and he died.\n\n5:32 And Noah was five hundred years old: and Noah begat Shem, Ham,\nand Japheth.\n\n6:1 And it came to pass, when men began to multiply on the face of the\nearth, and daughters were born unto them, 6:2 That the sons of God saw\nthe daughters of men that they were fair; and they took them wives of\nall which they chose.\n\n6:3 And the LORD said, My spirit shall not always strive with man, for\nthat he also is flesh: yet his days shall be an hundred and twenty\nyears.\n\n6:4 There were giants in the earth in those days; and also after that,\nwhen the sons of God came in unto the daughters of men, and they bare\nchildren to them, the same became mighty men which were of old, men of\nrenown.\n\n6:5 And God saw that the wickedness of man was great in the earth, and\nthat every imagination of the thoughts of his heart was only evil\ncontinually.\n\n6:6 And it repented the LORD that he had made man on the earth, and it\ngrieved him at his heart.\n\n6:7 And the LORD said, I will destroy man whom I have created from the\nface of the earth; both man, and beast, and the creeping thing, and\nthe fowls of the air; for it repenteth me that I have made them.\n\n6:8 But Noah found grace in the eyes of the LORD.\n\n6:9 These are the generations of Noah: Noah was a just man and perfect\nin his generations, and Noah walked with God.\n\n6:10 And Noah begat three sons, Shem, Ham, and Japheth.\n\n6:11 The earth also was corrupt before God, and the earth was filled\nwith violence.\n\n6:12 And God looked upon the earth, and, behold, it was corrupt; for\nall flesh had corrupted his way upon the earth.\n\n6:13 And God said unto Noah, The end of all flesh is come before me;\nfor the earth is filled with violence through them; and, behold, I\nwill destroy them with the earth.\n\n6:14 Make thee an ark of gopher wood; rooms shalt thou make in the\nark, and shalt pitch it within and without with pitch.\n\n6:15 And this is the fashion which thou shalt make it of: The length\nof the ark shall be three hundred cubits, the breadth of it fifty\ncubits, and the height of it thirty cubits.\n\n6:16 A window shalt thou make to the ark, and in a cubit shalt thou\nfinish it above; and the door of the ark shalt thou set in the side\nthereof; with lower, second, and third stories shalt thou make it.\n\n6:17 And, behold, I, even I, do bring a flood of waters upon the\nearth, to destroy all flesh, wherein is the breath of life, from under\nheaven; and every thing that is in the earth shall die.\n\n6:18 But with thee will I establish my covenant; and thou shalt come\ninto the ark, thou, and thy sons, and thy wife, and thy sons' wives\nwith thee.\n\n6:19 And of every living thing of all flesh, two of every sort shalt\nthou bring into the ark, to keep them alive with thee; they shall be\nmale and female.\n\n6:20 Of fowls after their kind, and of cattle after their kind, of\nevery creeping thing of the earth after his kind, two of every sort\nshall come unto thee, to keep them alive.\n\n6:21 And take thou unto thee of all food that is eaten, and thou shalt\ngather it to thee; and it shall be for food for thee, and for them.\n\n6:22 Thus did Noah; according to all that God commanded him, so did\nhe.\n\n7:1 And the LORD said unto Noah, Come thou and all thy house into the\nark; for thee have I seen righteous before me in this generation.\n\n7:2 Of every clean beast thou shalt take to thee by sevens, the male\nand his female: and of beasts that are not clean by two, the male and\nhis female.\n\n7:3 Of fowls also of the air by sevens, the male and the female; to\nkeep seed alive upon the face of all the earth.\n\n7:4 For yet seven days, and I will cause it to rain upon the earth\nforty days and forty nights; and every living substance that I have\nmade will I destroy from off the face of the earth.\n\n7:5 And Noah did according unto all that the LORD commanded him.\n\n7:6 And Noah was six hundred years old when the flood of waters was\nupon the earth.\n\n7:7 And Noah went in, and his sons, and his wife, and his sons' wives\nwith him, into the ark, because of the waters of the flood.\n\n7:8 Of clean beasts, and of beasts that are not clean, and of fowls,\nand of every thing that creepeth upon the earth, 7:9 There went in two\nand two unto Noah into the ark, the male and the female, as God had\ncommanded Noah.\n\n7:10 And it came to pass after seven days, that the waters of the\nflood were upon the earth.\n\n7:11 In the six hundredth year of Noah's life, in the second month,\nthe seventeenth day of the month, the same day were all the fountains\nof the great deep broken up, and the windows of heaven were opened.\n\n7:12 And the rain was upon the earth forty days and forty nights.\n\n7:13 In the selfsame day entered Noah, and Shem, and Ham, and Japheth,\nthe sons of Noah, and Noah's wife, and the three wives of his sons\nwith them, into the ark; 7:14 They, and every beast after his kind,\nand all the cattle after their kind, and every creeping thing that\ncreepeth upon the earth after his kind, and every fowl after his kind,\nevery bird of every sort.\n\n7:15 And they went in unto Noah into the ark, two and two of all\nflesh, wherein is the breath of life.\n\n7:16 And they that went in, went in male and female of all flesh, as\nGod had commanded him: and the LORD shut him in.\n\n7:17 And the flood was forty days upon the earth; and the waters\nincreased, and bare up the ark, and it was lift up above the earth.\n\n7:18 And the waters prevailed, and were increased greatly upon the\nearth; and the ark went upon the face of the waters.\n\n7:19 And the waters prevailed exceedingly upon the earth; and all the\nhigh hills, that were under the whole heaven, were covered.\n\n7:20 Fifteen cubits upward did the waters prevail; and the mountains\nwere covered.\n\n7:21 And all flesh died that moved upon the earth, both of fowl, and\nof cattle, and of beast, and of every creeping thing that creepeth\nupon the earth, and every man: 7:22 All in whose nostrils was the\nbreath of life, of all that was in the dry land, died.\n\n7:23 And every living substance was destroyed which was upon the face\nof the ground, both man, and cattle, and the creeping things, and the\nfowl of the heaven; and they were destroyed from the earth: and Noah\nonly remained alive, and they that were with him in the ark.\n\n7:24 And the waters prevailed upon the earth an hundred and fifty\ndays.\n\n8:1 And God remembered Noah, and every living thing, and all the\ncattle that was with him in the ark: and God made a wind to pass over\nthe earth, and the waters asswaged; 8:2 The fountains also of the deep\nand the windows of heaven were stopped, and the rain from heaven was\nrestrained; 8:3 And the waters returned from off the earth\ncontinually: and after the end of the hundred and fifty days the\nwaters were abated.\n\n8:4 And the ark rested in the seventh month, on the seventeenth day of\nthe month, upon the mountains of Ararat.\n\n8:5 And the waters decreased continually until the tenth month: in the\ntenth month, on the first day of the month, were the tops of the\nmountains seen.\n\n8:6 And it came to pass at the end of forty days, that Noah opened the\nwindow of the ark which he had made: 8:7 And he sent forth a raven,\nwhich went forth to and fro, until the waters were dried up from off\nthe earth.\n\n8:8 Also he sent forth a dove from him, to see if the waters were\nabated from off the face of the ground; 8:9 But the dove found no rest\nfor the sole of her foot, and she returned unto him into the ark, for\nthe waters were on the face of the whole earth: then he put forth his\nhand, and took her, and pulled her in unto him into the ark.\n\n8:10 And he stayed yet other seven days; and again he sent forth the\ndove out of the ark; 8:11 And the dove came in to him in the evening;\nand, lo, in her mouth was an olive leaf pluckt off: so Noah knew that\nthe waters were abated from off the earth.\n\n8:12 And he stayed yet other seven days; and sent forth the dove;\nwhich returned not again unto him any more.\n\n8:13 And it came to pass in the six hundredth and first year, in the\nfirst month, the first day of the month, the waters were dried up from\noff the earth: and Noah removed the covering of the ark, and looked,\nand, behold, the face of the ground was dry.\n\n8:14 And in the second month, on the seven and twentieth day of the\nmonth, was the earth dried.\n\n8:15 And God spake unto Noah, saying, 8:16 Go forth of the ark, thou,\nand thy wife, and thy sons, and thy sons' wives with thee.\n\n8:17 Bring forth with thee every living thing that is with thee, of\nall flesh, both of fowl, and of cattle, and of every creeping thing\nthat creepeth upon the earth; that they may breed abundantly in the\nearth, and be fruitful, and multiply upon the earth.\n\n8:18 And Noah went forth, and his sons, and his wife, and his sons'\nwives with him: 8:19 Every beast, every creeping thing, and every\nfowl, and whatsoever creepeth upon the earth, after their kinds, went\nforth out of the ark.\n\n8:20 And Noah builded an altar unto the LORD; and took of every clean\nbeast, and of every clean fowl, and offered burnt offerings on the\naltar.\n\n8:21 And the LORD smelled a sweet savour; and the LORD said in his\nheart, I will not again curse the ground any more for man's sake; for\nthe imagination of man's heart is evil from his youth; neither will I\nagain smite any more every thing living, as I have done.\n\n8:22 While the earth remaineth, seedtime and harvest, and cold and\nheat, and summer and winter, and day and night shall not cease.\n\n9:1 And God blessed Noah and his sons, and said unto them, Be\nfruitful, and multiply, and replenish the earth.\n\n9:2 And the fear of you and the dread of you shall be upon every beast\nof the earth, and upon every fowl of the air, upon all that moveth\nupon the earth, and upon all the fishes of the sea; into your hand are\nthey delivered.\n\n9:3 Every moving thing that liveth shall be meat for you; even as the\ngreen herb have I given you all things.\n\n9:4 But flesh with the life thereof, which is the blood thereof, shall\nye not eat.\n\n9:5 And surely your blood of your lives will I require; at the hand of\nevery beast will I require it, and at the hand of man; at the hand of\nevery man's brother will I require the life of man.\n\n9:6 Whoso sheddeth man's blood, by man shall his blood be shed: for in\nthe image of God made he man.\n\n9:7 And you, be ye fruitful, and multiply; bring forth abundantly in\nthe earth, and multiply therein.\n\n9:8 And God spake unto Noah, and to his sons with him, saying, 9:9 And\nI, behold, I establish my covenant with you, and with your seed after\nyou; 9:10 And with every living creature that is with you, of the\nfowl, of the cattle, and of every beast of the earth with you; from\nall that go out of the ark, to every beast of the earth.\n\n9:11 And I will establish my covenant with you, neither shall all\nflesh be cut off any more by the waters of a flood; neither shall\nthere any more be a flood to destroy the earth.\n\n9:12 And God said, This is the token of the covenant which I make\nbetween me and you and every living creature that is with you, for\nperpetual generations: 9:13 I do set my bow in the cloud, and it shall\nbe for a token of a covenant between me and the earth.\n\n9:14 And it shall come to pass, when I bring a cloud over the earth,\nthat the bow shall be seen in the cloud: 9:15 And I will remember my\ncovenant, which is between me and you and every living creature of all\nflesh; and the waters shall no more become a flood to destroy all\nflesh.\n\n9:16 And the bow shall be in the cloud; and I will look upon it, that\nI may remember the everlasting covenant between God and every living\ncreature of all flesh that is upon the earth.\n\n9:17 And God said unto Noah, This is the token of the covenant, which\nI have established between me and all flesh that is upon the earth.\n\n9:18 And the sons of Noah, that went forth of the ark, were Shem, and\nHam, and Japheth: and Ham is the father of Canaan.\n\n9:19 These are the three sons of Noah: and of them was the whole earth\noverspread.\n\n9:20 And Noah began to be an husbandman, and he planted a vineyard:\n9:21 And he drank of the wine, and was drunken; and he was uncovered\nwithin his tent.\n\n9:22 And Ham, the father of Canaan, saw the nakedness of his father,\nand told his two brethren without.\n\n9:23 And Shem and Japheth took a garment, and laid it upon both their\nshoulders, and went backward, and covered the nakedness of their\nfather; and their faces were backward, and they saw not their father's\nnakedness.\n\n9:24 And Noah awoke from his wine, and knew what his younger son had\ndone unto him.\n\n9:25 And he said, Cursed be Canaan; a servant of servants shall he be\nunto his brethren.\n\n9:26 And he said, Blessed be the LORD God of Shem; and Canaan shall be\nhis servant.\n\n9:27 God shall enlarge Japheth, and he shall dwell in the tents of\nShem; and Canaan shall be his servant.\n\n9:28 And Noah lived after the flood three hundred and fifty years.\n\n9:29 And all the days of Noah were nine hundred and fifty years: and\nhe died.\n\n10:1 Now these are the generations of the sons of Noah, Shem, Ham, and\nJapheth: and unto them were sons born after the flood.\n\n10:2 The sons of Japheth; Gomer, and Magog, and Madai, and Javan, and\nTubal, and Meshech, and Tiras.\n\n10:3 And the sons of Gomer; Ashkenaz, and Riphath, and Togarmah.\n\n10:4 And the sons of Javan; Elishah, and Tarshish, Kittim, and\nDodanim.\n\n10:5 By these were the isles of the Gentiles divided in their lands;\nevery one after his tongue, after their families, in their nations.\n\n10:6 And the sons of Ham; Cush, and Mizraim, and Phut, and Canaan.\n\n10:7 And the sons of Cush; Seba, and Havilah, and Sabtah, and Raamah,\nand Sabtechah: and the sons of Raamah; Sheba, and Dedan.\n\n10:8 And Cush begat Nimrod: he began to be a mighty one in the earth.\n\n10:9 He was a mighty hunter before the LORD: wherefore it is said,\nEven as Nimrod the mighty hunter before the LORD.\n\n10:10 And the beginning of his kingdom was Babel, and Erech, and\nAccad, and Calneh, in the land of Shinar.\n\n10:11 Out of that land went forth Asshur, and builded Nineveh, and the\ncity Rehoboth, and Calah, 10:12 And Resen between Nineveh and Calah:\nthe same is a great city.\n\n10:13 And Mizraim begat Ludim, and Anamim, and Lehabim, and Naphtuhim,\n10:14 And Pathrusim, and Casluhim, (out of whom came Philistim,) and\nCaphtorim.\n\n10:15 And Canaan begat Sidon his first born, and Heth, 10:16 And the\nJebusite, and the Amorite, and the Girgasite, 10:17 And the Hivite,\nand the Arkite, and the Sinite, 10:18 And the Arvadite, and the\nZemarite, and the Hamathite: and afterward were the families of the\nCanaanites spread abroad.\n\n10:19 And the border of the Canaanites was from Sidon, as thou comest\nto Gerar, unto Gaza; as thou goest, unto Sodom, and Gomorrah, and\nAdmah, and Zeboim, even unto Lasha.\n\n10:20 These are the sons of Ham, after their families, after their\ntongues, in their countries, and in their nations.\n\n10:21 Unto Shem also, the father of all the children of Eber, the\nbrother of Japheth the elder, even to him were children born.\n\n10:22 The children of Shem; Elam, and Asshur, and Arphaxad, and Lud,\nand Aram.\n\n10:23 And the children of Aram; Uz, and Hul, and Gether, and Mash.\n\n10:24 And Arphaxad begat Salah; and Salah begat Eber.\n\n10:25 And unto Eber were born two sons: the name of one was Peleg; for\nin his days was the earth divided; and his brother's name was Joktan.\n\n10:26 And Joktan begat Almodad, and Sheleph, and Hazarmaveth, and\nJerah, 10:27 And Hadoram, and Uzal, and Diklah, 10:28 And Obal, and\nAbimael, and Sheba, 10:29 And Ophir, and Havilah, and Jobab: all these\nwere the sons of Joktan.\n\n10:30 And their dwelling was from Mesha, as thou goest unto Sephar a\nmount of the east.\n\n10:31 These are the sons of Shem, after their families, after their\ntongues, in their lands, after their nations.\n\n10:32 These are the families of the sons of Noah, after their\ngenerations, in their nations: and by these were the nations divided\nin the earth after the flood.\n"

            text_object = Text.objects.create(
                text=text_raw
            )

            for i in range(10):
                rand_start, rand_end = get_rand_start_end(text_raw)
                Annotation.objects.create(text=text_object, start=rand_start, end=rand_end)


            print(f"starting mutation iteration: {mutation_iteration}")

            randomize_and_compare(text_object, mutation_iteration)
