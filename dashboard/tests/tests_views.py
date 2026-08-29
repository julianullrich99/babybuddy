# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test import Client as HttpClient
from django.contrib.auth import get_user_model
from django.core.management import call_command

from faker import Faker

from babybuddy.models import Settings
from core.models import ActivityType, Child


class ViewsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super(ViewsTestCase, cls).setUpClass()
        fake = Faker()
        call_command("migrate", verbosity=0)

        cls.c = HttpClient()

        fake_user = fake.simple_profile()
        cls.credentials = {
            "username": fake_user["username"],
            "password": fake.password(),
        }
        cls.user = get_user_model().objects.create_user(
            is_superuser=True, **cls.credentials
        )

        cls.c.login(**cls.credentials)

    def test_dashboard_views(self):
        page = self.c.get("/dashboard/")
        self.assertEqual(page.url, "/welcome/")

        call_command("fake", verbosity=0, children=1, days=1)
        child = Child.objects.first()
        page = self.c.get("/dashboard/")
        self.assertEqual(page.url, "/children/{}/dashboard/".format(child.slug))

        page = self.c.get("/dashboard/")
        self.assertEqual(page.url, "/children/{}/dashboard/".format(child.slug))
        # Test the actual child dashboard (including cards).
        # TODO: Test cards more granularly.
        page = self.c.get("/children/{}/dashboard/".format(child.slug))
        self.assertEqual(page.status_code, 200)

        Child.objects.create(
            first_name="Second", last_name="Child", birth_date="2000-01-01"
        )
        page = self.c.get("/dashboard/")
        self.assertEqual(page.status_code, 200)

    def test_child_dashboard_activity_cards(self):
        call_command("fake", verbosity=0, children=1, days=1)
        child = Child.objects.first()
        activity_type = ActivityType.objects.create(name="Bath Time")
        url = "/children/{}/dashboard/".format(child.slug)

        page = self.c.get(url)
        self.assertEqual(page.status_code, 200)
        self.assertIn(activity_type, page.context["visible_activity_types"])
        self.assertContains(page, "Bath Time")

        # An emoji is used in place of the icon font glyph when one is set.
        activity_type.emoji = "\U0001f6c1"
        activity_type.save()
        page = self.c.get(url)
        self.assertContains(page, "\U0001f6c1")

        # Inactive activity types do not get a card.
        activity_type.active = False
        activity_type.save()
        page = self.c.get(url)
        self.assertNotIn(activity_type, page.context["visible_activity_types"])

    def test_child_dashboard_card_order(self):
        call_command("fake", verbosity=0, children=1, days=1)
        child = Child.objects.first()
        url = "/children/{}/dashboard/".format(child.slug)

        page = self.c.get(url)
        card_ids = [card["id"] for card in page.context["dashboard_cards"]]
        self.assertEqual(card_ids[0], "timer_list")

        settings = Settings.objects.get(user=self.user)
        settings.dashboard_card_order = ["statistics", "sleep_last"]
        settings.save()

        page = self.c.get(url)
        card_ids = [card["id"] for card in page.context["dashboard_cards"]]
        self.assertEqual(card_ids[:2], ["statistics", "sleep_last"])
        # Cards missing from the stored order are appended, not dropped.
        self.assertIn("timer_list", card_ids)

    def test_child_dashboard_card_order_excludes_hidden(self):
        call_command("fake", verbosity=0, children=1, days=1)
        child = Child.objects.first()
        url = "/children/{}/dashboard/".format(child.slug)

        settings = Settings.objects.get(user=self.user)
        settings.dashboard_card_order = ["statistics", "sleep_last"]
        settings.dashboard_hidden_cards = ["statistics"]
        settings.save()

        page = self.c.get(url)
        card_ids = [card["id"] for card in page.context["dashboard_cards"]]
        self.assertNotIn("statistics", card_ids)
        self.assertEqual(card_ids[0], "sleep_last")

    def test_child_dashboard_card_order_includes_activity_types(self):
        call_command("fake", verbosity=0, children=1, days=1)
        child = Child.objects.first()
        activity_type = ActivityType.objects.create(name="Order Test")
        url = "/children/{}/dashboard/".format(child.slug)

        settings = Settings.objects.get(user=self.user)
        settings.dashboard_card_order = [activity_type.card_id]
        settings.save()

        page = self.c.get(url)
        cards = page.context["dashboard_cards"]
        self.assertEqual(cards[0]["id"], activity_type.card_id)
        self.assertEqual(cards[0]["activity_type"], activity_type)

    def test_child_dashboard_hidden_cards(self):
        call_command("fake", verbosity=0, children=1, days=1)
        child = Child.objects.first()
        url = "/children/{}/dashboard/".format(child.slug)

        page = self.c.get(url)
        self.assertIn("statistics", page.context["visible_cards"])

        self.user.settings.dashboard_hidden_cards = ["statistics"]
        self.user.settings.save()

        page = self.c.get(url)
        self.assertNotIn("statistics", page.context["visible_cards"])
