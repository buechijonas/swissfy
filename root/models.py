from django.contrib.auth import get_user_model
from django.db import models
from django.forms import ValidationError
from django.template.defaultfilters import linebreaksbr
from django.utils.timezone import now
from django.utils.translation import gettext as _

User = get_user_model()


# Create your models here.
class Role(models.Model):
    ROLE_CHOICES = [
        ("Admin", "Admin"),
        ("Moderator", "Moderator"),
        ("Verifiziert", "Verifiziert"),
        ("Standard", "Standard"),
    ]

    name = models.CharField(
        max_length=50, choices=ROLE_CHOICES, verbose_name=_("Rolle")
    )
    priority = models.IntegerField(verbose_name=_("Stufe"))

    def __str__(self):
        return f"Role: {self.name}, Stufe: {self.priority}"


class LegalUser(models.Model):
    privacy = models.BooleanField(verbose_name=_("Datenschutzerklärung"), default=False)
    disclaimer = models.BooleanField(
        verbose_name=_("Haftungsausschluss"), default=False
    )
    terms = models.BooleanField(verbose_name=_("Nutzungsrichtlinien"), default=False)

    protection = models.BooleanField(
        verbose_name=_("Pädophilenschutz"),
        null=True,
        blank=True,
        default=None,
    )

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, verbose_name=_("Benutzer")
    )

    def __str__(self):
        return _("Legal User: {username}").format(username=self.user.username)


class ConfigUser(models.Model):
    role = models.ForeignKey(
        Role, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Rolle")
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Benutzer"),
        related_name="config",
    )

    def __str__(self):
        return _("Config User: {username}").format(username=self.user.username)


class SocialUser(models.Model):
    friends = models.ManyToManyField(
        User,
        related_name="friends_with",
        blank=True,
        verbose_name=_("Freunde"),
    )
    sent_requests = models.ManyToManyField(
        User,
        related_name="sent_friend_requests",
        blank=True,
        verbose_name=_("Gesendete Anfragen"),
    )
    received_requests = models.ManyToManyField(
        User,
        related_name="received_friend_requests",
        blank=True,
        verbose_name=_("Erhaltene Anfragen"),
    )
    blocked = models.ManyToManyField(
        User,
        related_name="blocked",
        blank=True,
        verbose_name=_("Blockiert"),
    )
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, verbose_name=_("Benutzer")
    )

    def __str__(self):
        return _("Social User: {username}").format(username=self.user.username)


class DetailUser(models.Model):
    class Sex(models.TextChoices):
        MALE = "male", _("Männlich")
        FEMALE = "female", _("Weiblich")
        DIVERS = "divers", _("Divers")

    class Relationship(models.TextChoices):
        SINGLE = "single", _("Single")
        GETTING_TO_KNOW = "getting_to_know", _("Kennenlernphase")
        IN_RELATIONSHIP = "in_relationship", _("In einer Beziehung")
        ENGAGED = "engaged", _("Verlobt")
        MARRIED = "married", _("Verheiratet")
        COMPLICATED = "complicated", _("Es ist kompliziert")
        SEPARATED = "separated", _("Getrennt")
        DIVORCED = "divorced", _("Geschieden")
        WIDOWED = "widowed", _("Verwitwet")
        OTHER = "other", _("Sonstiges")

    biography = models.TextField(
        max_length=500, null=True, blank=True, verbose_name=_("Biografie")
    )
    sex = models.CharField(
        max_length=50, choices=Sex.choices, verbose_name=_("Geschlecht")
    )
    birthday = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Geburtstag"),
    )
    profession = models.CharField(
        max_length=50, null=True, blank=True, verbose_name=_("Tätigkeit")
    )
    place_of_residence = models.CharField(max_length=100, verbose_name=_("Wohnort"))
    place_of_origin = models.CharField(max_length=100, verbose_name=_("Heimatort"))
    relationship = models.CharField(
        max_length=50, choices=Relationship.choices, verbose_name=_("Beziehungsstatus")
    )
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, verbose_name=_("Benutzer")
    )

    def clean(self):
        # Überprüfen, ob der Geburtstag in der Zukunft liegt
        if self.birthday and self.birthday > now().date():
            raise ValidationError(
                {"birthday": _("Das Geburtsdatum darf nicht in der Zukunft liegen.")}
            )

    def format_biography(self):
        return linebreaksbr(self.biographie)

    def __str__(self):
        return _("Detail User: {username}").format(username=self.user.username)


class Nickname(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="nicknamed",
        verbose_name=_("Benutzer, der Nicknames vergibt"),
    )

    nicknamed = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="nicknamer",
        verbose_name=_("Benutzer, der einen Nickname erhält"),
    )

    nickname = models.CharField(max_length=100, verbose_name=_("Nickname"))

    def __str__(self):
        return f"{self.user.username} -> {self.target_user.username}: {self.nickname}"
