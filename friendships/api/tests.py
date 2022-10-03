from testing.testcases import TestCase
from rest_framework.test import APIClient
from friendships.models import Friendship

FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWEINGS_URL = '/api/friendships/{}/followings/'


class FriendshipApiTestCases(TestCase):

    def setUp(self):
        #self.anonymous_client = APIClient()
        self.testuser1 = self.create_user('testuser1')
        self.testuser1_client = APIClient()
        self.testuser1_client.force_authenticate(self.testuser1)

        self.testuser2 = self.create_user('testuser2')
        self.testuser2_client = APIClient()
        self.testuser2_client.force_authenticate(self.testuser2)

        for i in range(2):
            follower = self.create_user('testuser2_follower{}'.format(i))
            Friendship.objects.create(from_user=follower, to_user=self.testuser2)

        for i in range(3):
            following = self.create_user('testuser2_following{}'.format(i))
            Friendship.objects.create(from_user=self.testuser2, to_user=following)

    def test_follow(self):
        url = FOLLOW_URL.format(self.testuser1.id)
        # test login
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)
        # test post
        response = self.testuser2_client.get(url)
        self.assertEqual(response.status_code, 405)
        # test follow myself
        response = self.testuser1_client.post(url)
        self.assertEqual(response.status_code, 400)
        # test follow non-existting user
        url_1 = FOLLOW_URL.format(self.testuser1.id + 10000)
        response = self.testuser1_client.post(url_1)
        self.assertEqual(response.status_code, 404)

        # positive test
        response = self.testuser2_client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], self.testuser1.username)
        self.assertEqual(response.data['user']['id'], self.testuser1.id)

        # duplicated follow
        response = self.testuser2_client.post(url)
        self.assertEqual(response.status_code, 400)
        # self.assertEqual(response.status_code, 201)
        # self.assertEqual(response.data['duplicated'], True)

        count = Friendship.objects.count()
        response = self.testuser1_client.post(FOLLOW_URL.format(self.testuser2.id))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Friendship.objects.count(), count + 1)

    def test_unfollow(self):
        url = UNFOLLOW_URL.format(self.testuser1.id)

        # test login
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)
        # test post
        response = self.testuser2_client.get(url)
        self.assertEqual(response.status_code, 405)
        # test follow myself
        response = self.testuser1_client.post(url)
        self.assertEqual(response.status_code, 400)
        # test follow non-existting user
        url_1 = FOLLOW_URL.format(self.testuser1.id + 10000)
        response = self.testuser2_client.post(url_1)
        self.assertEqual(response.status_code, 404)

        # positive test
        Friendship.objects.create(from_user=self.testuser2, to_user=self.testuser1)
        count = Friendship.objects.count()
        response = self.testuser2_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(Friendship.objects.count(), count - 1)

        # unfollow a nonfollowing user
        count = Friendship.objects.count()
        response = self.testuser2_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(Friendship.objects.count(), count)

    def test_followings(self):
        url = FOLLOWEINGS_URL.format(self.testuser2.id)
        # test post
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # postive test for anonymous get
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followings']), 3)
        # test order
        ts0 = response.data['followings'][0]['created_at']
        ts1 = response.data['followings'][1]['created_at']
        ts2 = response.data['followings'][2]['created_at']
        self.assertEqual(ts0 > ts1 > ts2, True)
        self.assertEqual(
            response.data['followings'][0]['user']['username'],
            'testuser2_following2'
        )
        self.assertEqual(
            response.data['followings'][1]['user']['username'],
            'testuser2_following1'
        )
        self.assertEqual(
            response.data['followings'][2]['user']['username'],
            'testuser2_following0'
        )

    def test_followers(self):
        url = FOLLOWERS_URL.format(self.testuser2.id)
        # test post
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # postive test for anonymous get
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followers']), 2)
        # test order
        ts0 = response.data['followers'][0]['created_at']
        ts1 = response.data['followers'][1]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(
            response.data['followers'][0]['user']['username'],
            'testuser2_follower1'
        )
        self.assertEqual(
            response.data['followers'][1]['user']['username'],
            'testuser2_follower0'
        )








