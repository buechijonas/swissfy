import json
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"


def load(name):
    return json.loads((DATA / f"{name}.json").read_text())


TEXTS = load("achievements")
THEMES = load("themes")
EGGS = load("eggs")
