def incr_likes_count(sender, instance, created, **kwargs):
    from django.db.models import F
    from weits.models import Weit
    from comments.models import Comment

    if not created:
        return
    model_class = instance.content_type.model_class()
    if model_class != Weit:
        Comment.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') + 1)
        return
    # don't use following implementation, they are not atomic operation
    # weit = instance.content_object
    # weit.likes_count += 1
    # weit.save()
    # or
    # Weit.objects.filter(id=instance.object_id).update(likes_count=instance.likes_count + 1)

    # sql: update likes_count=likes_count+1 from weits_table where id=instance.object_id
    # F expression 可以直接在数据库中操作字段的值，而不需要把字段load到内存，再从内存改完后存会数据库
    # 1. 这样效率更高 2. 可以避免race condition
    # method 1, but update can not trigger post save for weit
    Weit.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') + 1)

    # method 2 , use save here, so it can trigger post_save listener of Weit
    # weit = instance.content_object
    # weit.likes_count = F('likes_count') + 1
    # weit.save()


def decr_likes_count(sender, instance, **kwargs):
    from django.db.models import F
    from weits.models import Weit
    from comments.models import Comment

    model_class = instance.content_type.model_class()
    if model_class != Weit:
        Comment.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') - 1)
        return
    # UPDATE can not trigger post_save for weit
    Weit.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') - 1)
