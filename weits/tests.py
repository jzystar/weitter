from datetime import timedelta
from testing.testcases import TestCase
from utils.redis_client import RedisClient
from utils.redis_serializers import DjangoModelSerializer
from utils.time_helpers import utc_now
from weits.constants import WeitPhotoStatus
from weits.models import WeitPhoto
from weits.services import WeitService
from weitter.cache import USER_WEITS_PATTERN


class WeitTest(TestCase):

    def setUp(self):
        super(WeitTest, self).setUp()
        self.user = self.create_user('user1')
        self.weit = self.create_weit(self.user)

    def test_hours_to_now(self):
        self.weit.created_at = utc_now() - timedelta(hours=10)
        self.weit.save()
        self.assertEqual(self.weit.hours_to_now, 10)

    def test_like_set(self):
        self.create_like(self.user, self.weit)
        self.assertEqual(self.weit.like_set.count(), 1)
        self.create_like(self.user, self.weit)
        self.assertEqual(self.weit.like_set.count(), 1)

        user2 = self.create_user(username='user2')
        self.create_like(user2, self.weit)
        self.assertEqual(self.weit.like_set.count(), 2)

    def test_create_photo(self):
        photo = WeitPhoto.objects.create(
            weit=self.weit,
            user=self.user,
        )

        self.assertEqual(photo.user, self.user)
        self.assertEqual(photo.status, WeitPhotoStatus.PENDING)
        self.assertEqual(self.weit.weitphoto_set.count(), 1)

    def test_cache_weit_in_redis(self):
        weit = self.create_weit(self.user)
        conn = RedisClient.get_connection()
        serialized_data = DjangoModelSerializer.serialize(weit)
        conn.set(f'weit:{weit.id}', serialized_data)
        data = conn.get('weit:not_exists')
        self.assertEqual(data, None)

        data = conn.get(f'weit:{weit.id}')
        cached_weit = DjangoModelSerializer.deserialize(data)
        self.assertEqual(weit, cached_weit)


class WeitServiceTest(TestCase):
    def setUp(self):
        super(WeitServiceTest, self).setUp()
        self.user = self.create_user('user')

    def test_get_user_weits(self):
        weit_ids = []
        for i in range(3):
            weit = self.create_weit(self.user, 'weit {}'.format(i))
            weit_ids.append(weit.id)
        weit_ids = weit_ids[::-1]

        conn = RedisClient.get_connection()

        # cache miss
        weits = WeitService.get_cached_weits(self.user.id)
        self.assertEqual([w.id for w in weits], weit_ids)

        # cache hit
        weits = WeitService.get_cached_weits(self.user.id)
        self.assertEqual([w.id for w in weits], weit_ids)

        # cache update
        new_weit = self.create_weit(self.user, 'new weit content')
        weits = WeitService.get_cached_weits(self.user.id)
        weit_ids.insert(0, new_weit.id)
        self.assertEqual([w.id for w in weits], weit_ids)

    def test_create_new_weit_before_get_cached_weits(self):
        weit1 = self.create_weit(self.user, 'weit1')
        RedisClient.clear()

        conn = RedisClient.get_connection()

        key = USER_WEITS_PATTERN.format(user_id=self.user.id)
        self.assertEqual(conn.exists(key), False)
        weit2 = self.create_weit(self.user, 'weit2')
        self.assertEqual(conn.exists(key), True)

        weits = WeitService.get_cached_weits(self.user.id)
        self.assertEqual([w.id for w in weits], [weit2.id, weit1.id])
