from django.contrib import admin

from root.models import ConfigUser
from root.models import DetailUser
from root.models import FollowRelation
from root.models import LegalUser
from root.models import LinkedUser
from root.models import Nickname
from root.models import NotificationPost
from root.models import Post
from root.models import Role
from root.models import SocialUser


# Register your models here.
admin.site.register(LegalUser)
admin.site.register(ConfigUser)
admin.site.register(SocialUser)
admin.site.register(DetailUser)
admin.site.register(LinkedUser)
admin.site.register(FollowRelation)
admin.site.register(Role)
admin.site.register(Nickname)
admin.site.register(Post)
admin.site.register(NotificationPost)
