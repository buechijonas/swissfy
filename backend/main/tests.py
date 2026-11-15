from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import translation

from .numbers import compact_number


class CompactNumberTests(SimpleTestCase):
    def test_compact_number(self):
        cases = {
            0: "0",
            1: "1",
            1000: "1000",
            9999: "9999",
            10_000: "10 Tsd.",
            12_345: "12 Tsd.",
            100_000: "100 Tsd.",
            999_999: "999 Tsd.",
            1_000_000: "1M",
            1_250_000: "1.2M",
            15_000_000: "15M",
            -12_000: "-12 Tsd.",
        }
        for value, expected in cases.items():
            self.assertEqual(compact_number(value), expected)


class OptionsTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create(username="anna"))

    def test_options_on_a_viewset_without_queryset_answers(self):
        response = self.client.options("/api/chats/protection/")
        self.assertEqual(response.status_code, 200)

    def test_options_on_a_model_viewset_answers(self):
        response = self.client.options("/api/posts/")
        self.assertEqual(response.status_code, 200)


@override_settings(LANGUAGE_CODE="en")
class LanguageTests(TestCase):
    def missing_version(self, **headers):
        return self.client.get("/api/docs/changelogs/9.9.9/", headers=headers).json()["detail"]

    def test_english_is_the_fallback(self):
        self.assertEqual(self.missing_version(), "This version does not exist.")

    def test_unsupported_browser_language_falls_back_to_english(self):
        detail = self.missing_version(accept_language="pt-BR")
        self.assertEqual(detail, "This version does not exist.")

    def test_browser_language_is_used_without_cookie(self):
        detail = self.missing_version(accept_language="fr-CH,de;q=0.8")
        self.assertEqual(detail, "Cette version n'existe pas.")

    def test_german_browser_gets_the_source_text(self):
        detail = self.missing_version(accept_language="de-CH")
        self.assertEqual(detail, "Diese Version gibt es nicht.")

    def test_language_cookie_wins_over_the_browser(self):
        self.client.cookies["language"] = "it"
        detail = self.missing_version(accept_language="de")
        self.assertEqual(detail, "Questa versione non esiste.")

    def test_romansh_is_supported(self):
        self.client.cookies["language"] = "rm"
        self.assertEqual(self.missing_version(), "Questa versiun n'exista betg.")

    def test_chinese_browser_gets_simplified_chinese(self):
        self.assertEqual(self.missing_version(accept_language="zh-CN"), "此版本不存在。")

    def test_compact_numbers_follow_the_language(self):
        with translation.override("en"):
            self.assertEqual(compact_number(12_345), "12K")
