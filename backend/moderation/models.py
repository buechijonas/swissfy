from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Q

from posts.models import Comment, Post


class Reason(models.TextChoices):
    ANTISEMITISM = "antisemitism", "Antisemitismus"
    EXPLOITATION = "exploitation", "Ausbeuterische Inhalte"
    INSULT = "insult", "Beleidigung"
    REWARD_HUNTING = "reward_hunting", "Belohnungsjagd"
    HARASSMENT = "harassment", "Belästigung"
    FRAUD = "fraud", "Betrug"
    CHRISTOPHOBIA = "christophobia", "Christophobie"
    CYBERGROOMING = "cybergrooming", "Cybergrooming"
    CYBERBULLYING = "cyberbullying", "Cybermobbing"
    DISCRIMINATION = "discrimination", "Diskriminierung"
    DOXXING = "doxxing", "Doxxing"
    THREAT = "threat", "Drohung"
    EXTORTION = "extortion", "Erpressung"
    MISINFORMATION = "misinformation", "Falschinformationen"
    FASCISM = "fascism", "Faschismus"
    XENOPHOBIA = "xenophobia", "Fremdenfeindlichkeit"
    CONSPIRACY = "conspiracy", "Gefährliche Verschwörungstheorien"
    VIOLENT_CONTENT = "violent_content", "Gewaltbasierter Inhalt"
    GLORIFYING_VIOLENCE = "glorifying_violence", "Gewaltverherrlichung"
    HATE_SPEECH = "hate_speech", "Hassrede"
    HOMOPHOBIA = "homophobia", "Homophobie"
    IDENTITY_THEFT = "identity_theft", "Identitätsdiebstahl"
    ILLEGAL_CONTENT = "illegal_content", "Illegale Inhalte"
    ISLAMOPHOBIA = "islamophobia", "Islamophobie"
    CULTURAL_APPROPRIATION = "cultural_appropriation", "Kulturelle Aneignung"
    PROTECTION_OF_MINORS = "protection_of_minors", "Minderjährigenschutz"
    PRIVILEGE_ABUSE = "privilege_abuse", "Missbrauch von Privilegien"
    PLAGIARISM = "plagiarism", "Plagiate"
    PORNOGRAPHY = "pornography", "Pornografische Inhalte"
    PROPAGANDA = "propaganda", "Propaganda"
    RACISM = "racism", "Rassismus"
    RELATIVIZATION = "relativization", "Relativierung"
    SELF_HARM = "self_harm", "Selbstgefährdung"
    VIGILANTISM = "vigilantism", "Selbstjustiz"
    SEXISM = "sexism", "Sexismus"
    SEXTORTION = "sextortion", "Sextortion"
    SPAM = "spam", "Spam"
    INAPPROPRIATE_LANGUAGE = "inappropriate_language", "Unangemessene Wortwahl"
    UNETHICAL_ADVERTISING = "unethical_advertising", "Unethische Werbung"
    WHATABOUTISM = "whataboutism", "Whataboutismus"


WARNING_EXPIRY = timedelta(days=90)

ONE_TARGET = Q(post__isnull=False, comment__isnull=True) | Q(
    post__isnull=True, comment__isnull=False
)


class Report(models.Model):
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, null=True, blank=True, related_name="reports"
    )
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, null=True, blank=True, related_name="reports"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=ONE_TARGET, name="report_one_target"),
            models.UniqueConstraint(fields=["reporter", "post"], name="unique_post_report"),
            models.UniqueConstraint(fields=["reporter", "comment"], name="unique_comment_report"),
        ]
        indexes = [
            models.Index(
                fields=["post", "comment"],
                condition=Q(resolved_at__isnull=True),
                name="open_reports",
            )
        ]


class Warning(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="warnings"
    )
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    reason = models.CharField(max_length=40, choices=Reason.choices)
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["post"], condition=Q(post__isnull=False), name="one_warning_per_post"
            ),
            models.UniqueConstraint(
                fields=["comment"],
                condition=Q(comment__isnull=False),
                name="one_warning_per_comment",
            ),
        ]


class Suspension(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="suspensions"
    )
    warning = models.ForeignKey(Warning, on_delete=models.SET_NULL, null=True, related_name="+")
    step = models.PositiveSmallIntegerField()
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-starts_at"]
        indexes = [models.Index(fields=["user", "ends_at"], name="suspension_user_end")]
