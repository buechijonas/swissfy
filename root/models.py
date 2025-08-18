from datetime import timedelta

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
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, verbose_name=_("Benutzer")
    )

    follow = models.ManyToManyField(
        User,
        related_name="followed",
        blank=True,
        verbose_name="Folgt",
        through="FollowRelation",
        through_fields=(
            "from_user",
            "to_user",
        ),
    )

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

    def __str__(self):
        return _("Social User: {username}").format(username=self.user.username)


class FollowRelation(models.Model):
    from_user = models.ForeignKey(
        SocialUser, on_delete=models.CASCADE, related_name="following_relation"
    )
    to_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="follower_relation"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Gefolgt seit")

    def __str__(self):
        return f"{self.from_user.user.username} folgt {self.to_user.username} seit {self.created_at}"


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

    image = models.ImageField(
        upload_to="user_images/",
        null=True,
        blank=True,
        verbose_name=_("Profilbild"),
        help_text=_("Lade ein Bild für dein Profil hoch."),
    )

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


class LinkedUser(models.Model):
    discord = models.CharField(
        max_length=20, null=True, blank=True, verbose_name=_("Discord Benutzername")
    )
    epicgames = models.CharField(
        max_length=20, null=True, blank=True, verbose_name=_("Epic Games Benutzername")
    )
    facebook = models.CharField(
        max_length=20, null=True, blank=True, verbose_name=_("Facebook Benutzername")
    )
    instagram = models.CharField(
        max_length=20, null=True, blank=True, verbose_name=_("Instagram Benutzername")
    )
    linkedin = models.CharField(
        max_length=20, null=True, blank=True, verbose_name=_("LinkedIn Benutzername")
    )
    pinterest = models.CharField(
        max_length=20, null=True, blank=True, verbose_name=_("Pinterest Benutzername")
    )
    playstation = models.CharField(
        max_length=20, null=True, blank=True, verbose_name=_("PlayStation Benutzername")
    )
    reddit = models.CharField(
        max_length=20, null=True, blank=True, verbose_name=_("Reddit Benutzername")
    )
    snapchat = models.CharField(
        max_length=20, null=True, blank=True, verbose_name=_("Snapchat Benutzername")
    )
    steam = models.CharField(
        max_length=20, null=True, blank=True, verbose_name=_("Steam Benutzername")
    )
    threads = models.CharField(
        max_length=20, null=True, blank=True, verbose_name=_("Threads Benutzername")
    )
    tiktok = models.CharField(
        max_length=20, null=True, blank=True, verbose_name=_("Tiktok Benutzername")
    )
    twitter = models.CharField(
        max_length=20, null=True, blank=True, verbose_name=_("Tiktok Benutzername")
    )
    xbox = models.CharField(
        max_length=20, null=True, blank=True, verbose_name=_("Xbox Benutzername")
    )
    youtube = models.CharField(
        max_length=20, null=True, blank=True, verbose_name=_("YouTube Kanalname")
    )
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, verbose_name=_("Benutzer")
    )

    def __str__(self):
        return _("Linked User: {username}").format(username=self.user.username)


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


class Post(models.Model):
    image = models.ImageField(
        upload_to="posts/",
        null=True,
        blank=True,
        verbose_name=_("Post Bild"),
        help_text=_("Lade ein Bild für dein Profil hoch."),
    )
    text = models.TextField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Erstellt am"))
    likes = models.ManyToManyField(
        User, related_name="liked", blank=True, verbose_name=_("Gefällt mir")
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posted",
        verbose_name=_("Autor"),
    )

    class Meta:
        ordering = ["-created_at"]

    def get_time_display(self):
        now_time = now()
        diff = now_time - self.created_at

        if diff < timedelta(seconds=1):
            return _("Vor 1 Sekunde")
        elif diff < timedelta(minutes=1):
            return _("Vor {} Sekunden").format(diff.seconds)
        elif diff < timedelta(minutes=2):
            return _("Vor 1 Minute")
        elif diff < timedelta(hours=1):
            return _("Vor {} Minuten").format(diff.seconds // 60)
        elif diff < timedelta(hours=2):
            return _("Vor 1 Stunde")
        elif diff < timedelta(days=1):
            return _("Vor {} Stunden").format(diff.seconds // 3600)
        elif diff < timedelta(days=2):
            return _("Gestern")
        elif diff < timedelta(days=365):
            return _("Am {:%d.%m}").format(self.created_at)
        else:
            return _("{:%d.%m.%Y}").format(self.created_at)

    def __str__(self):
        return f"Post by {self.author.username} at {self.get_time_display()}"


class NotificationPost(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="post_notificated",
        verbose_name="Post",
    )
    read_by = models.ManyToManyField(
        User,
        related_name="read_post_notification",
        blank=True,
        verbose_name=_("Aktivitäten gelesen"),
    )


class Commentary(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="commentaries",
        verbose_name=_("Post"),
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="commentaries",
        verbose_name=_("Autor"),
    )
    text = models.TextField(
        max_length=500,
        verbose_name=_("Kommentartext"),
        help_text=_("Schreibe einen Kommentar (max. 500 Zeichen)."),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Erstellt am"))

    class Meta:
        ordering = ["created_at"]
        verbose_name = _("Kommentar")
        verbose_name_plural = _("Kommentare")

    def __str__(self):
        return f"{self.author.username} – {self.text[:30]}..."
