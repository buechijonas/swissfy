from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

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

    class PictureAudience(models.TextChoices):
        FOLLOWERS = "followers", "Follower"
        FRIENDS = "friends", "Freunde"
        GROUPS = "groups", "Gruppen"

    class ChatProtection(models.TextChoices):
        STANDARD = "standard", "Standard"
        DEVICE = "device", "Nur auf diesem Gerät"
        PIN = "pin", "Chat-PIN"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    govex_sub = models.CharField(max_length=64, unique=True, null=True, blank=True)

    avatar = models.CharField(
        max_length=20, blank=True, default="", choices=[(a, a) for a in AVATAR_CHOICES]
    )
    public_picture = models.FileField("Öffentliches Profilbild", upload_to="profiles/", blank=True)
    private_picture = models.FileField("Privates Profilbild", upload_to="profiles/", blank=True)
    private_picture_visibility = models.CharField(
        "Privates Profilbild sichtbar für",
        max_length=20,
        choices=PictureAudience.choices,
        default=PictureAudience.FRIENDS,
    )
    private_picture_groups = models.ManyToManyField(
        "posts.ContactGroup", related_name="+", blank=True
    )
    birthdate = models.DateField("Geburtsdatum", null=True, blank=True)

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
    chat_protection = models.CharField(
        "Chat-Verschlüsselung",
        max_length=20,
        choices=ChatProtection.choices,
        default=ChatProtection.STANDARD,
    )
    read_receipts = models.BooleanField("Lesebestätigungen", default=True)
    chat_requests = models.BooleanField("Chat-Anfragen erlauben", default=True)
    show_birthdate = models.BooleanField("Geburtsdatum anzeigen", default=False)

    def __str__(self):
        return f"Profile({self.user})"


@receiver(post_delete, sender=UserProfile)
def delete_profile_pictures(sender, instance, **kwargs):
    instance.public_picture.delete(save=False)
    instance.private_picture.delete(save=False)


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
