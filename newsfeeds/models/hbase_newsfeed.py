from django.contrib.auth.models import User
from django_hbase import models
from weits.models import Weit
from utils.memcached_helper import MemcachedHelper


class HBaseNewsFeed(models.HBaseModel):
    user_id = models.IntegerField(reverse=True)
    created_at = models.TimestampField()
    weit_id = models.IntegerField(column_family='cf')

    class Meta:
        table_name = 'weitter_newsfeed'
        row_key = ('user_id', 'created_at')

    def __str__(self):
        return f'{self.created_at} inbox of {self.user_id}: {self.weit_id}'

    @property
    def cached_weit(self):
        return MemcachedHelper.get_object_through_cache(Weit, self.weit_id)

    @property
    def cached_user(self):
        return MemcachedHelper.get_object_through_cache(User, self.user_id)
