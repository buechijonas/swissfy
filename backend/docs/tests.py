import tempfile
from pathlib import Path

from django.test import TestCase, override_settings


class ChangelogTests(TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        settings = override_settings(CHANGELOG_DIR=self.directory)
        settings.enable()
        self.addCleanup(settings.disable)

    def write(self, version, bump, notes):
        content = f"---\nbump: {bump}\ndate: 2026-11-10\n---\n\n{notes}\n"
        (self.directory / f"v{version}.md").write_text(content)

    def test_lists_changelogs_newest_version_first(self):
        self.write("0.9.0", "minor", "- feat: nine")
        self.write("0.10.0", "minor", "- feat: ten")
        self.write("0.10.1", "patch", "- fix: ten one")

        response = self.client.get("/api/docs/changelogs/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [changelog["version"] for changelog in response.json()],
            ["0.10.1", "0.10.0", "0.9.0"],
        )

    def test_renders_notes_as_sanitized_markdown(self):
        self.write("1.0.0", "major", "- feat: **bold**\n- <script>alert(1)</script>")

        response = self.client.get("/api/docs/changelogs/1.0.0/")

        self.assertEqual(response.status_code, 200)
        changelog = response.json()
        self.assertEqual(changelog["bump"], "major")
        self.assertEqual(changelog["date"], "2026-11-10")
        self.assertIn("<strong>bold</strong>", changelog["html"])
        self.assertNotIn("<script>", changelog["html"])

    def test_unknown_version_is_not_found(self):
        response = self.client.get("/api/docs/changelogs/9.9.9/")

        self.assertEqual(response.status_code, 404)

    def test_is_public(self):
        self.write("1.0.0", "major", "- feat: public")

        response = self.client.get("/api/docs/changelogs/")

        self.assertEqual(response.status_code, 200)
