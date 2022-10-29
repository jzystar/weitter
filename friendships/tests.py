from testing.testcases import TestCase
from friendships.models import Friendship
from friendships.services import FriendshipServices

class FriendshipServiceTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.user1 = self.create_user('user1')
        self.user2 = self.create_user('user2')

    def test_get_followings(self):
        tester1 = self.create_user('tester1')
        tester2 = self.create_user('tester2')

        for to_user in [tester1, tester2, self.user2]:
            Friendship.objects.create(from_user=self.user1, to_user=to_user)

        FriendshipServices.invalidate_following_cache(self.user1.id)

        user_id_set = FriendshipServices.get_following_user_id_set(self.user1.id)
        self.assertEqual(user_id_set, {tester1.id, tester2.id, self.user2.id})
        Friendship.objects.filter(from_user=self.user1, to_user=self.user2).delete()
        FriendshipServices.invalidate_following_cache(self.user1.id)
        user_id_set = FriendshipServices.get_following_user_id_set(self.user1.id)
        self.assertEqual(user_id_set, {tester1.id, tester2.id})
