from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save, pre_delete
from likes.models import Like
from utils.listeners import invalidate_object_cache
from utils.memcached_helper import MemcachedHelper
from utils.time_helpers import utc_now
from weits.constants import WeitPhotoStatus, WEIT_PHOTO_STATUS_CHOICES
from weits.listeners import push_weit_to_cache


class Weit(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        help_text="who posts this weit",
        verbose_name=u"发帖人",
    )
    content = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = (('user', 'created_at'), )
        ordering = ('user', '-created_at')

    def __str__(self):
        return f'{self.created_at} {self.user}: {self.content}'

    @property
    def hours_to_now(self):
        return (utc_now() - self.created_at).seconds // 3600

    @property
    def like_set(self):
        return Like.objects.filter(
            content_type=ContentType.objects.get_for_model(Weit),
            object_id=self.id,
        ).order_by('-created_at')

    @property
    def cached_user(self):
        return MemcachedHelper.get_object_through_cache(User, self.user_id)


class WeitPhoto(models.Model):
    weit = models.ForeignKey(Weit, on_delete=models.SET_NULL, null=True)

    # can be accessed by weit instance, but it's more convinient to add user as ForeignKey here
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    file = models.FileField()
    order = models.IntegerField(default=0)

    # for review usage
    status = models.IntegerField(
        default=WeitPhotoStatus.PENDING,
        choices=WEIT_PHOTO_STATUS_CHOICES,
    )

    # soft delete, 直接删除会影响效率，后面可以通过异步任务进行文件删除
    has_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = (
            ('user', 'created_at'),
            ('has_deleted', 'created_at'),
            ('status', 'created_at'),
            ('weit', 'order'),
        )

    def __str__(self):
        return f'{self.weit.id}: {self.file}'


post_save.connect(invalidate_object_cache, sender=Weit)
pre_delete.connect(invalidate_object_cache, sender=Weit)
# 目前没有修改操作，但是若加入weit的修改，这里会有问题，save会直接向redis lpush修改后的weit，
# 而不是修改redis中对应的那个weit，若做修改的化我们很难从redis中定位到要修改的那个weit进行更新
# 解决方式：
# 1。跟memcached一样，有修改就直接把对应的redis cache 删掉
# 2。用二级缓存，我们一级缓存redis只存该用户的weit id的list，二级缓存memcached存储weit的所有内容
# 一级缓存redis可以存list的特性来存一串id，通过这个id再去二级缓存memcache里面拿，每次更新都只更新memcache的数据，
# 不过每次memcache取数据时，需要检查该id是否已经缓存了，没有的话需要记录缺失的ids再去db中取
post_save.connect(push_weit_to_cache, sender=Weit)
