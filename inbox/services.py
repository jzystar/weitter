from comments.models import Comment
from django.contrib.contenttypes.models import ContentType
from notifications.signals import notify
from weits.models import Weit


class NotificationService(object):

    @classmethod
    def send_like_notification(cls, like):
        target = like.content_object
        if target.user == like.user:
            return
        if like.content_type == ContentType.objects.get_for_model(Weit):
            notify.send(
                like.user,
                recipient=target.user,
                verb="liked your weit",
                target=target,
            )
        if like.content_type == ContentType.objects.get_for_model(Comment):
            notify.send(
                like.user,
                recipient=target.user,
                verb="liked your comment",
                target=target,
            )

    @classmethod
    def send_comment_notification(cls, comment):
        target = comment.weit
        if target.user == comment.user:
            return
        notify.send(
            comment.user,
            recipient=target.user,
            verb="commented on your weit",
            target=target,
        )
