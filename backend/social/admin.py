from django.contrib import admin

from .models import Block, FriendRequest, Friendship, Nickname


@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ["sender", "receiver", "created_at"]


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ["user", "friend", "created_at"]


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ["user", "blocked", "created_at"]


@admin.register(Nickname)
class NicknameAdmin(admin.ModelAdmin):
    list_display = ["owner", "target", "nickname"]
