from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from newsfeeds.listeners import push_newsfeed_to_cache
from utils.memcached_helper import MemcachedHelper
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


# bulk_create will not trigger this post_save signal
post_save.connect(push_newsfeed_to_cache, sender=NewsFeed)
