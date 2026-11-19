from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from commons.models import EncryptedTextField

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
        MALE = "male", _("Male")
        FEMALE = "female", _("Female")
        DIVERS = "divers", _("Diverse")

    class Relationship(models.TextChoices):
        SINGLE = "single", _("Single")
        GETTING_TO_KNOW = "getting_to_know", _("Getting to know someone")
        IN_RELATIONSHIP = "in_relationship", _("In a relationship")
        ENGAGED = "engaged", _("Engaged")
        MARRIED = "married", _("Married")
        COMPLICATED = "complicated", _("It's complicated")
        SEPARATED = "separated", _("Separated")
        DIVORCED = "divorced", _("Divorced")
        WIDOWED = "widowed", _("Widowed")
        OTHER = "other", _("Other")

    class Visibility(models.TextChoices):
        PUBLIC = "public", _("Public")
        FOLLOWERS = "followers", _("Followers only")
        FRIENDS = "friends", _("Friends only")

    class PictureAudience(models.TextChoices):
        FOLLOWERS = "followers", _("Followers")
        FRIENDS = "friends", _("Friends")
        GROUPS = "groups", _("Groups")

    class ChatProtection(models.TextChoices):
        STANDARD = "standard", _("Standard")
        DEVICE = "device", _("Only on this device")
        PIN = "pin", _("Chat PIN")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    govex_sub = models.CharField(max_length=64, unique=True, null=True, blank=True)

    avatar = models.CharField(
        max_length=20, blank=True, default="", choices=[(a, a) for a in AVATAR_CHOICES]
    )
    public_picture = models.FileField(
        _("Public profile picture"), upload_to="profiles/", blank=True
    )
    private_picture = models.FileField(
        _("Private profile picture"), upload_to="profiles/", blank=True
    )
    private_picture_visibility = models.CharField(
        _("Private profile picture visible to"),
        max_length=20,
        choices=PictureAudience.choices,
        default=PictureAudience.FRIENDS,
    )
    private_picture_groups = models.ManyToManyField(
        "posts.ContactGroup", related_name="+", blank=True
    )
    birthdate = models.DateField(_("Birthdate"), null=True, blank=True)

    biography = EncryptedTextField(_("Biography"), max_length=500, blank=True)
    sex = models.CharField(_("Sex"), max_length=20, choices=Sex.choices, blank=True)
    profession = models.CharField(_("Occupation"), max_length=50, blank=True)
    place_of_residence = models.CharField(_("Place of residence"), max_length=100, blank=True)
    place_of_origin = models.CharField(_("Place of origin"), max_length=100, blank=True)
    relationship = models.CharField(
        _("Relationship status"), max_length=20, choices=Relationship.choices, blank=True
    )
    favorite_movies = models.JSONField(_("Favourite movies"), default=list, blank=True)
    favorite_series = models.JSONField(_("Favourite series"), default=list, blank=True)
    favorite_games = models.JSONField(_("Favourite games"), default=list, blank=True)

    profile_visibility = models.CharField(
        _("Profile visible to"),
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
    )
    chat_protection = models.CharField(
        _("Chat encryption"),
        max_length=20,
        choices=ChatProtection.choices,
        default=ChatProtection.STANDARD,
    )
    read_receipts = models.BooleanField(_("Read receipts"), default=True)
    chat_requests = models.BooleanField(_("Allow chat requests"), default=True)
    show_birthdate = models.BooleanField(_("Show birthdate"), default=False)

    def __str__(self):
        return f"Profile({self.user})"

    @property
    def has_public_picture(self):
        return bool(self.public_picture)

    @property
    def requires_follow_request(self):
        return self.profile_visibility != self.Visibility.PUBLIC

    @property
    def pictures(self):
        return {"public": self.public_picture, "private": self.private_picture}

    @property
    def favorites(self):
        return {
            "favorite_movies": self.favorite_movies,
            "favorite_series": self.favorite_series,
            "favorite_games": self.favorite_games,
        }


@receiver(post_delete, sender=UserProfile)
def delete_profile_pictures(sender, instance, **kwargs):
    instance.public_picture.delete(save=False)
    instance.private_picture.delete(save=False)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


class UserConsent(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="consent"
    )
    privacy = models.BooleanField(_("Privacy policy"), default=False)
    terms = models.BooleanField(_("Terms of use"), default=False)
    disclaimer = models.BooleanField(_("Disclaimer"), default=False)

    FIELDS = ["privacy", "terms", "disclaimer"]

    def __str__(self):
        return f"Consent({self.user})"

    @property
    def status(self):
        return {"privacy": self.privacy, "terms": self.terms, "disclaimer": self.disclaimer}

    def accept(self, field):
        UserConsent.objects.filter(pk=self.pk).update(**{field: True})
        self.refresh_from_db(fields=[field])


def user_consent(user):
    consent, _ = UserConsent.objects.get_or_create(user=user)
    return consent


class DeviceToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="device_tokens"
    )
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"DeviceToken({self.user})"
