from datetime import timedelta
from testing.testcases import TestCase
from utils.redis_client import RedisClient
from utils.redis_serializers import DjangoModelSerializer
from utils.time_helpers import utc_now
from weits.constants import WeitPhotoStatus
from weits.models import WeitPhoto


class WeitTest(TestCase):

    def setUp(self):
        self.clear_cache()
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
