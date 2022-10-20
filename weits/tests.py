from datetime import timedelta

from django.contrib.auth.models import User
from testing.testcases import TestCase

# Create your tests here.
from utils.time_helpers import utc_now
from weits.models import WeitPhoto
from weits.constants import WeitPhotoStatus


class WeitTest(TestCase):

    def setUp(self):
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

    def test_weit_photo(self):
        photo = WeitPhoto.objects.create(
            weit=self.weit,
            user=self.user,
        )

        self.assertEqual(photo.user, self.user)
        self.assertEqual(photo.status, WeitPhotoStatus.PENDING)
        self.assertEqual(self.weit.weitphoto_set.count(), 1)
