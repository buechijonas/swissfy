from datetime import date
from functools import cache, cached_property

from django.conf import settings
from rest_framework.exceptions import NotFound

from commons.markdown import render


class Changelog:
    def __init__(self, path):
        _, header, notes = path.read_text().split("---\n", 2)
        self.path = path
        self.meta = dict(line.split(": ", 1) for line in header.strip().splitlines())
        self.notes = notes.strip()

    @property
    def version(self):
        return self.path.stem.removeprefix("v")

    @property
    def version_key(self):
        return tuple(int(part) for part in self.version.split("."))

    @property
    def bump(self):
        return self.meta["bump"]

    @property
    def date(self):
        return date.fromisoformat(self.meta["date"])

    @cached_property
    def html(self):
        return render(self.notes)

    @classmethod
    def all(cls):
        changelogs = [
            load(path, path.stat().st_mtime) for path in settings.CHANGELOG_DIR.glob("v*.md")
        ]
        return sorted(changelogs, key=lambda changelog: changelog.version_key, reverse=True)

    @classmethod
    def get(cls, version):
        path = settings.CHANGELOG_DIR / f"v{version}.md"
        if not path.is_file():
            raise NotFound("Diese Version gibt es nicht.")
        return load(path, path.stat().st_mtime)


@cache
def load(path, modified):
    return Changelog(path)
