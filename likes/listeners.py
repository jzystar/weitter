from django.db.models import F
from utils.redis_helper import RedisHelper


def incr_likes_count(sender, instance, created, **kwargs):
    from comments.models import Comment
    from weits.models import Weit

    if not created:
        return
    model_class = instance.content_type.model_class()
    if model_class != Weit:
        Comment.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') + 1)
    # don't use following implementation, they are not atomic operation
    # weit = instance.content_object
    # weit.likes_count += 1
    # weit.save()
    # or
    # Weit.objects.filter(id=instance.object_id).update(likes_count=instance.likes_count + 1)

    # sql: update likes_count=likes_count+1 from weits_table where id=instance.object_id
    # F expression 可以直接在数据库中操作字段的值，而不需要把字段load到内存，再从内存改完后存会数据库
    # 1. 这样效率更高 2. 可以避免race condition

    # method 1, but update can not trigger post save for weit, in this case
    # we don't want to update/delete cache when likes_count changed, since it changes frequently
    # so we cache likes_count separately even though it is in weit table.
    else:
        Weit.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') + 1)
    # update likes_count redis cache
    # TODO: Comment has not been cached, so right now we only cache likes_count for comment is meaningless
    RedisHelper.incr_count(instance.content_object, 'likes_count')


    # method 2 , use save here, it can trigger post_save listener of Weit
    # weit = instance.content_object
    # weit.likes_count = F('likes_count') + 1
    # weit.save()


def decr_likes_count(sender, instance, **kwargs):
    from comments.models import Comment
    from weits.models import Weit

    model_class = instance.content_type.model_class()
    if model_class != Weit:
        Comment.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') - 1)
    # UPDATE can not trigger post_save for weit
    else:
        Weit.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') - 1)
    # TODO: Comment has not been cached, so right now we only cache likes_count for comment is meaningless
    RedisHelper.decr_count(instance.content_object, 'likes_count')

