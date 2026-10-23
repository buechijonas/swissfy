import shutil
import tempfile

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from .tests import govex_user

TOKEN = "monolith-test-token"
URL = "/api/internal/profiles/{}/"
MEDIA = tempfile.mkdtemp()


@override_settings(MONOLITH_API_TOKEN=TOKEN, MEDIA_ROOT=MEDIA)
class InternalProfileTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.anna = govex_user("anna", "sub-anna")
        self.anna.first_name = "Anna"
        self.anna.last_name = "Muster"
        self.anna.save()

    def get(self, sub, token=TOKEN, path=""):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        return self.client.get(URL.format(sub) + path, headers=headers)

    def test_returns_profile_for_govex_sub(self):
        response = self.get("sub-anna")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "username": "anna",
                "first_name": "Anna",
                "last_name": "Muster",
                "avatar": "",
                "has_picture": False,
            },
        )

    def test_reports_existing_picture(self):
        self.anna.profile.public_picture.save("anna.webp", ContentFile(b"webp"))
        self.assertTrue(self.get("sub-anna").json()["has_picture"])

    def test_serves_public_picture(self):
        self.anna.profile.public_picture.save("anna.webp", ContentFile(b"webp"))
        response = self.get("sub-anna", path="picture/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/webp")
        self.assertEqual(b"".join(response.streaming_content), b"webp")

    def test_picture_is_404_without_public_picture(self):
        self.assertEqual(self.get("sub-anna", path="picture/").status_code, 404)

    def test_picture_rejects_missing_token(self):
        self.assertEqual(self.get("sub-anna", token=None, path="picture/").status_code, 403)

    def test_rejects_missing_token(self):
        self.assertEqual(self.get("sub-anna", token=None).status_code, 403)

    def test_rejects_wrong_token(self):
        self.assertEqual(self.get("sub-anna", token="wrong").status_code, 403)

    def test_rejects_session_user_without_token(self):
        self.client.force_login(self.anna)
        self.assertEqual(self.get("sub-anna", token=None).status_code, 403)

    @override_settings(MONOLITH_API_TOKEN=None)
    def test_disabled_without_configured_token(self):
        self.assertEqual(self.get("sub-anna", token="None").status_code, 403)
        self.assertEqual(self.get("sub-anna", token="").status_code, 403)

    def test_unknown_sub_is_404(self):
        self.assertEqual(self.get("sub-unknown").status_code, 404)

    def test_inactive_user_is_404(self):
        self.anna.is_active = False
        self.anna.save()
        self.assertEqual(self.get("sub-anna").status_code, 404)
