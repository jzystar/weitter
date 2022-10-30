from django.contrib.auth.models import User
from django.db import models
from utils.memcached_helper import MemcachedHelper
from utils.listeners import invalidate_object_cache
from weits.models import Weit


class NewsFeed(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    weit = models.ForeignKey(Weit, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = (('user', 'created_at'),)
        unique_together = (('user', 'weit'),)
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.created_at} inbox of {self.user}: {self.weit}'

    @property
    def cached_weit(self):
        return MemcachedHelper.get_object_through_cache(Weit, self.weit_id)

