from .weit import Weit
from django.contrib.auth.models import User
from django.db import models
from weits.constants import WeitPhotoStatus, WEIT_PHOTO_STATUS_CHOICES


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
