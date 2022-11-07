from django.db.models import F
from utils.listeners import invalidate_object_cache
from utils.redis_helper import RedisHelper


def incr_comments_count(sender, instance, created, **kwargs):
    from weits.models import Weit

    if not created:
        return

    # handle the comment
    Weit.objects.filter(id=instance.weit_id).update(comments_count=F('comments_count') + 1)
    # invalidate_object_cache(sender=Weit, instance=instance.weit)
    RedisHelper.incr_count(instance.weit, 'comments_count')


def decr_comments_count(sender, instance, **kwargs):
    from weits.models import Weit

    # handle the comment
    Weit.objects.filter(id=instance.weit_id).update(comments_count=F('comments_count') - 1)
    # invalidate_object_cache(sender=Weit, instance=instance.weit)
    RedisHelper.decr_count(instance.weit, 'comments_count')


