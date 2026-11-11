from django.contrib import admin

from .models import UserConsent, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "govex_sub", "avatar"]
    search_fields = ["user__username", "govex_sub"]


@admin.register(UserConsent)
class UserConsentAdmin(admin.ModelAdmin):
    list_display = ["user", "privacy", "terms", "disclaimer"]
    search_fields = ["user__username"]
