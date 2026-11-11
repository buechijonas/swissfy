from pathlib import Path

from django.conf import settings

from commons.markdown import render


def changelog_dir():
    return Path(settings.CHANGELOG_DIR)


def version_key(version):
    return tuple(int(part) for part in version.split("."))


def parse(path):
    _, header, notes = path.read_text().split("---\n", 2)
    meta = dict(line.split(": ", 1) for line in header.strip().splitlines())
    return {
        "version": path.stem.removeprefix("v"),
        "bump": meta["bump"],
        "date": meta["date"],
        "html": render(notes.strip()),
    }


def all_changelogs():
    changelogs = [parse(path) for path in changelog_dir().glob("v*.md")]
    return sorted(changelogs, key=lambda changelog: version_key(changelog["version"]), reverse=True)


def changelog(version):
    path = changelog_dir() / f"v{version}.md"
    return parse(path) if path.is_file() else None
