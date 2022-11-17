from comments.models import Comment
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import caches
from django.test import TestCase as DjangoTestCase
from django_hbase.models import HBaseModel
from friendships.models import Friendship
from gatekeeper.models import GateKeeper
from likes.models import Like
from newsfeeds.models import NewsFeed
from rest_framework.test import APIClient
from utils.redis_client import RedisClient
from weits.models import Weit


class TestCase(DjangoTestCase):
    hbase_table_created = False

    def setUp(self):
        self.clear_cache()
        try:
            self.hbase_table_created = True
            for hbase_models_class in HBaseModel.__subclasses__():
                hbase_models_class.create_table()
        except Exception:
            self.tearDown()
            # 继续抛出异常
            raise

    def tearDown(self):
        if not self.hbase_table_created:
            return
        for hbase_models_class in HBaseModel.__subclasses__():
            hbase_models_class.drop_table()

    def clear_cache(self):
        caches['testing'].clear()
        RedisClient.clear()
        # open hbase switch for friendship
        # GateKeeper.set_kv('switch_friendship_to_hbase', 'percent', 100)

    @property
    def anonymous_client(self):
        if hasattr(self, '_anonymous_client'):
            return self._anonymous_client
        self._anonymous_client = APIClient()
        return self._anonymous_client

    def create_user(self, username, email=None, password=None):
        if password is None:
            password = 'generic password'
        if email is None:
            email = f'{username}@weitter.com'
        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

    def create_weit(self, user, content=None):
        if content is None:
            content = 'default weit content'
        return Weit.objects.create(user=user, content=content)

    def create_comment(self, user, weit, content=None):
        if content is None:
            content = 'default comment content'
        return Comment.objects.create(user=user, weit=weit, content=content)

    def create_like(self, user, target):
        return Like.objects.get_or_create(
            user=user,
            content_type=ContentType.objects.get_for_model(target),
            # content_type=ContentType.objects.get_for_model(target.__class__),
            object_id=target.id,
        )[0]

    def create_user_and_client(self, *args, **kwargs):
        user = self.create_user(*args, *kwargs)
        client = APIClient()
        client.force_authenticate(user)
        return user, client

    def create_newsfeed(self, user, weit):
        return NewsFeed.objects.create(user=user, weit=weit)

    def create_friendship(self, from_user, to_user):
        return Friendship.objects.create(from_user=from_user, to_user=to_user)
