from django_hbase.models import BadRowKeyError, EmptyColumnError
from friendships.models import Friendship, HBaseFollower, HBaseFollowing
from friendships.services import FriendshipServices
from testing.testcases import TestCase

import time


class FriendshipServiceTests(TestCase):

    def setUp(self):
        super(FriendshipServiceTests, self).setUp()
        self.user1 = self.create_user('user1')
        self.user2 = self.create_user('user2')

    def test_get_followings(self):
        tester1 = self.create_user('tester1')
        tester2 = self.create_user('tester2')

        for to_user in [tester1, tester2, self.user2]:
            self.create_friendship(from_user=self.user1, to_user=to_user)
            #Friendship.objects.create(from_user=self.user1, to_user=to_user)

        FriendshipServices.invalidate_following_cache(self.user1.id)

        user_id_set = FriendshipServices.get_following_user_id_set(self.user1.id)
        self.assertEqual(user_id_set, {tester1.id, tester2.id, self.user2.id})
        FriendshipServices.unfollow(from_user_id=self.user1.id, to_user_id=self.user2.id)
        # Friendship.objects.filter(from_user=self.user1, to_user=self.user2).delete()
        FriendshipServices.invalidate_following_cache(self.user1.id)
        user_id_set = FriendshipServices.get_following_user_id_set(self.user1.id)
        self.assertEqual(user_id_set, {tester1.id, tester2.id})


class HBaseTests(TestCase):

    @property
    def ts_now(self):
        return int(time.time() * 1000000)

    def test_save_and_get(self):
        timestamp = self.ts_now
        following = HBaseFollowing(from_user_id=123, to_user_id=34, created_at=timestamp)
        following.save()

        instance = HBaseFollowing.get(from_user_id=123, created_at=timestamp)
        self.assertEqual(instance.from_user_id, 123)
        self.assertEqual(instance.to_user_id, 34)
        self.assertEqual(instance.created_at, timestamp)

        following.to_user_id = 456
        following.save()
        instance = HBaseFollowing.get(from_user_id=123, created_at=timestamp)
        self.assertEqual(instance.from_user_id, 123)
        self.assertEqual(instance.to_user_id, 456)
        self.assertEqual(instance.created_at, timestamp)

        # rowkey not exists, return None
        instance = HBaseFollowing.get(from_user_id=123, created_at=self.ts_now)
        self.assertEqual(instance, None)

    def test_create_and_get(self):
        # missing column data, can not store in hbase
        try:
            HBaseFollower.create(to_user_id=1, created_at=self.ts_now)
            exception_raised = False
        except EmptyColumnError:
            exception_raised = True
        self.assertEqual(exception_raised, True)

        # invalid row_key
        try:
            HBaseFollower.create(from_user_id=1, to_user_id=2)
            exception_raised = False
        except BadRowKeyError as e:
            exception_raised = True
            self.assertEqual(str(e), f"created_at is missing in row key of {HBaseFollower.__name__}")
        self.assertEqual(exception_raised, True)

        ts = self.ts_now
        HBaseFollower.create(from_user_id=1, created_at=ts, to_user_id=2)
        instance = HBaseFollower.get(to_user_id=2, created_at=ts)
        self.assertEqual(instance.from_user_id, 1)
        self.assertEqual(instance.to_user_id, 2)
        self.assertEqual(instance.created_at, ts)

        # can not get if row key is missing
        try:
            HBaseFollower.get(to_user_id=2)
            exception_raised = False
        except BadRowKeyError as e:
            exception_raised = True
            self.assertEqual(str(e), f"created_at is missing in row key of {HBaseFollower.__name__}")
        self.assertEqual(exception_raised, True)

    def test_filter(self):
        HBaseFollowing.create(from_user_id=1, to_user_id=2, created_at=self.ts_now)
        HBaseFollowing.create(from_user_id=1, to_user_id=3, created_at=self.ts_now)
        HBaseFollowing.create(from_user_id=1, to_user_id=4, created_at=self.ts_now)

        # test prefix
        followings = HBaseFollowing.filter(prefix=(1, ))
        self.assertEqual(3, len(followings))
        self.assertEqual(followings[0].from_user_id, 1)
        self.assertEqual(followings[0].to_user_id, 2)
        self.assertEqual(followings[1].from_user_id, 1)
        self.assertEqual(followings[1].to_user_id, 3)
        self.assertEqual(followings[2].from_user_id, 1)
        self.assertEqual(followings[2].to_user_id, 4)

        # test limit
        followings = HBaseFollowing.filter(prefix=(1, None), limit=1)
        self.assertEqual(len(followings), 1)
        self.assertEqual(followings[0].to_user_id, 2)

        followings = HBaseFollowing.filter(prefix=(1, None), limit=2)
        self.assertEqual(len(followings), 2)
        self.assertEqual(followings[0].to_user_id, 2)
        self.assertEqual(followings[1].to_user_id, 3)

        followings = HBaseFollowing.filter(prefix=(1, None), limit=4)
        self.assertEqual(len(followings), 3)
        self.assertEqual(followings[0].to_user_id, 2)
        self.assertEqual(followings[1].to_user_id, 3)
        self.assertEqual(followings[2].to_user_id, 4)

        # test start
        followings = HBaseFollowing.filter(start=(1, followings[1].created_at), limit=2)
        self.assertEqual(len(followings), 2)
        self.assertEqual(followings[0].to_user_id, 3)
        self.assertEqual(followings[1].to_user_id, 4)

        # test reverse
        followings = HBaseFollowing.filter(prefix=(1, ), limit=2, reverse=True)
        self.assertEqual(len(followings), 2)
        self.assertEqual(followings[0].to_user_id, 4)
        self.assertEqual(followings[1].to_user_id, 3)

        followings = HBaseFollowing.filter(start=(1, followings[1].created_at), limit=2, reverse=True)
        self.assertEqual(len(followings), 2)
        self.assertEqual(followings[0].to_user_id, 3)
        self.assertEqual(followings[1].to_user_id, 2)
