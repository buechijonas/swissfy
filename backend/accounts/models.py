from django.conf import settings
from django.db import models

# The avatars govex offers (govex-meta blueprint there).
AVATAR_CHOICES = [
    "bee",
    "bison",
    "camel",
    "cat",
    "chameleon",
    "crab",
    "deer",
    "dog",
    "dolphin",
    "duck",
    "elephant",
    "fish",
    "flamingo",
    "frog",
    "giraffe",
    "hedgehog",
    "hen",
    "hermit-crab",
    "hippopotamus",
    "horse",
    "jellyfish",
    "kangaroo",
    "kiwi",
    "koala",
    "lion",
    "llama",
    "lobster",
    "meerkat",
    "monkey",
    "octopus",
    "ostrich",
    "owl",
    "panda-bear",
    "parrot",
    "penguin",
    "pig",
    "rabbit",
    "seahorse",
    "seal",
    "shark",
    "sheep",
    "snail",
    "snake",
    "squid",
    "squirrel",
    "swan",
    "toucan",
    "turtle",
    "walrus",
    "whale",
]

# Roles are Django groups, created by migration 0002_roles. Every new account
# starts with this one.
DEFAULT_ROLE = "Standard"


class UserProfile(models.Model):
    class Sex(models.TextChoices):
        MALE = "male", "Männlich"
        FEMALE = "female", "Weiblich"
        DIVERS = "divers", "Divers"

    class Relationship(models.TextChoices):
        SINGLE = "single", "Single"
        GETTING_TO_KNOW = "getting_to_know", "Kennenlernphase"
        IN_RELATIONSHIP = "in_relationship", "In einer Beziehung"
        ENGAGED = "engaged", "Verlobt"
        MARRIED = "married", "Verheiratet"
        COMPLICATED = "complicated", "Es ist kompliziert"
        SEPARATED = "separated", "Getrennt"
        DIVORCED = "divorced", "Geschieden"
        WIDOWED = "widowed", "Verwitwet"
        OTHER = "other", "Sonstiges"

    class Visibility(models.TextChoices):
        PUBLIC = "public", "Öffentlich"
        FOLLOWERS = "followers", "Nur Follower"
        FRIENDS = "friends", "Nur Freunde"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    # The `sub` claim of this user's govex identity (authentik user UUID).
    govex_sub = models.CharField(max_length=64, unique=True, null=True, blank=True)

    # Managed in govex and taken over on every login and account update.
    avatar = models.CharField(
        max_length=20, blank=True, default="", choices=[(a, a) for a in AVATAR_CHOICES]
    )
    birthdate = models.DateField("Geburtsdatum", null=True, blank=True)

    # Managed in swissfy.
    biography = models.TextField("Biografie", max_length=500, blank=True)
    sex = models.CharField("Geschlecht", max_length=20, choices=Sex.choices, blank=True)
    profession = models.CharField("Tätigkeit", max_length=50, blank=True)
    place_of_residence = models.CharField("Wohnort", max_length=100, blank=True)
    place_of_origin = models.CharField("Heimatort", max_length=100, blank=True)
    relationship = models.CharField(
        "Beziehungsstatus", max_length=20, choices=Relationship.choices, blank=True
    )

    profile_visibility = models.CharField(
        "Profil sichtbar für", max_length=20, choices=Visibility.choices, default=Visibility.PUBLIC
    )

    def __str__(self):
        return f"Profile({self.user})"


def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


class UserConsent(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="consent"
    )
    privacy = models.BooleanField("Datenschutzerklärung", default=False)
    terms = models.BooleanField("Nutzungsrichtlinien", default=False)
    disclaimer = models.BooleanField("Haftungsausschluss", default=False)

    def __str__(self):
        return f"Consent({self.user})"
