from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase

# Create your tests here.
from utils.time_helpers import utc_now
from weits.models import Weit


class WeitTest(TestCase):

    def test_hours_to_now(self):
        user = User.objects.create_user('testuser', "testuser@test.com", "testpassword")
        weit = Weit.objects.create(user=user, content='unit test for weit hours to now')
        weit.created_at = utc_now() - timedelta(hours=10)
        weit.save()
        self.assertEqual(weit.hours_to_now, 10)