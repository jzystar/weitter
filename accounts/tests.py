from accounts.models import UserProfile
from testing.testcases import TestCase


class UserProfileTest(TestCase):

    def setUp(self):
        super(UserProfileTest, self).setUp()

    def test_profile_property(self):
        user1 = self.create_user('user1')
        p = user1.profile
        self.assertEqual(isinstance(p, UserProfile), True)
        self.assertEqual(UserProfile.objects.count(), 1)
