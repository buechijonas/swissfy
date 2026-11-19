from django.apps import AppConfig
from django.utils.autoreload import autoreload_started

from .content import DATA


def watch_content(sender, **kwargs):
    sender.watch_dir(DATA, "*.json")


class AchievementsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "swissfy.achievements"

    def ready(self):
        autoreload_started.connect(watch_content)
