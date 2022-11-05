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


# 1. bulk_create will not trigger this post_save signal
# 2. 若某个user的信息改变了，比如昵称，那我们redis cache中的数据不会有负面影响，因为newsfeed是存的user_id和weit_id，
# 对于其中weit中的user，会去找cached_user和cached_profile，他们都会在model层面更新时invalidate，所以不会有影响。
post_save.connect(push_newsfeed_to_cache, sender=NewsFeed)
