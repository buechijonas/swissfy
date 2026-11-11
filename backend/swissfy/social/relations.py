from commons.exceptions import BadRequest
from swissfy.notifications.models import Notification
from swissfy.notifications.notify import notify, resolve_request, withdraw

from .models import Follow, FollowRequest, FriendRequest, Friendship

Kind = Notification.Kind
Resolution = Notification.Resolution


def follows(follower, following):
    return Follow.objects.filter(follower=follower, following=following).exists()


def are_friends(user, other):
    return Friendship.objects.filter(user=user, friend=other).exists()


def follow(viewer, target):
    if target.profile.requires_follow_request and not follows(viewer, target):
        _, created = FollowRequest.objects.get_or_create(follower=viewer, following=target)
        kind = Kind.FOLLOW_REQUEST
    else:
        _, created = Follow.objects.get_or_create(follower=viewer, following=target)
        kind = Kind.FOLLOW
    if created:
        notify(target, kind, actor=viewer)


def unfollow(viewer, target):
    Follow.objects.filter(follower=viewer, following=target).delete()
    withdraw(target, Kind.FOLLOW, viewer)
    FollowRequest.objects.filter(follower=viewer, following=target).delete()
    withdraw(target, Kind.FOLLOW_REQUEST, viewer, resolution="")


def send_friend_request(viewer, target):
    if not (follows(viewer, target) and follows(target, viewer)):
        raise BadRequest("Freundschaftsanfragen gehen nur, wenn ihr euch gegenseitig folgt.")
    if are_friends(viewer, target):
        raise BadRequest("Ihr seid bereits befreundet.")
    _, created = FriendRequest.objects.get_or_create(sender=viewer, receiver=target)
    if created:
        notify(target, Kind.FRIEND_REQUEST, actor=viewer)


def decide_follow_request(follow_request, accepted):
    resolution = Resolution.ACCEPTED if accepted else Resolution.DECLINED
    resolve_request(
        follow_request.following, Kind.FOLLOW_REQUEST, follow_request.follower, resolution
    )
    if accepted:
        follow_request.accept()
    else:
        follow_request.delete()


def decide_friend_request(friend_request, accepted):
    resolution = Resolution.ACCEPTED if accepted else Resolution.DECLINED
    resolve_request(friend_request.receiver, Kind.FRIEND_REQUEST, friend_request.sender, resolution)
    if accepted:
        friend_request.accept()
    else:
        friend_request.delete()


def accept_open_follow_requests(user):
    for follow_request in user.received_follow_requests.select_related("follower", "following"):
        decide_follow_request(follow_request, accepted=True)
