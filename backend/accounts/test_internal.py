from django.test import TestCase, override_settings

from .tests import govex_user

TOKEN = "monolith-test-token"
URL = "/api/internal/profiles/{}/"


@override_settings(MONOLITH_API_TOKEN=TOKEN)
class InternalProfileTests(TestCase):
    def setUp(self):
        self.anna = govex_user("anna", "sub-anna")
        self.anna.first_name = "Anna"
        self.anna.last_name = "Muster"
        self.anna.save()

    def get(self, sub, token=TOKEN):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        return self.client.get(URL.format(sub), headers=headers)

    def test_returns_profile_for_govex_sub(self):
        response = self.get("sub-anna")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"username": "anna", "first_name": "Anna", "last_name": "Muster"}
        )

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
