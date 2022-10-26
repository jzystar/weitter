from testing.testcases import TestCase
from rest_framework.test import APIClient
from friendships.models import Friendship
from utils.pagination import FriendshipPagination

FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


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
        url = FOLLOWINGS_URL.format(self.testuser2.id)
        # test post
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # postive test for anonymous get
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        # test order
        ts0 = response.data['results'][0]['created_at']
        ts1 = response.data['results'][1]['created_at']
        ts2 = response.data['results'][2]['created_at']
        self.assertEqual(ts0 > ts1 > ts2, True)
        self.assertEqual(
            response.data['results'][0]['user']['username'],
            'testuser2_following2'
        )
        self.assertEqual(
            response.data['results'][1]['user']['username'],
            'testuser2_following1'
        )
        self.assertEqual(
            response.data['results'][2]['user']['username'],
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
        self.assertEqual(len(response.data['results']), 2)
        # test order
        ts0 = response.data['results'][0]['created_at']
        ts1 = response.data['results'][1]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(
            response.data['results'][0]['user']['username'],
            'testuser2_follower1'
        )
        self.assertEqual(
            response.data['results'][1]['user']['username'],
            'testuser2_follower0'
        )
    
    def test_followers_pagination(self):
        max_page_size = FriendshipPagination.max_page_size
        page_size = FriendshipPagination.page_size
        for i in range(page_size * 2):
            follower = self.create_user('testuser1_follower{}'.format(i))
            Friendship.objects.create(from_user=follower, to_user=self.testuser1)
            if follower.id % 2 == 0:
                Friendship.objects.create(from_user=self.testuser2, to_user=follower)

        url = FOLLOWERS_URL.format(self.testuser1.id)
        self._test_friendship_pagination(url, page_size, max_page_size)

        # anonymous hasn't followed any users
        response = self.anonymous_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        response = self.testuser2_client.get(url, {'page': 1})
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)
    
    def test_followings_pagination(self):
        max_page_size = FriendshipPagination.max_page_size
        page_size = FriendshipPagination.page_size
        for i in range(page_size * 2):
            following = self.create_user('testuser1_following{}'.format(i))
            Friendship.objects.create(from_user=self.testuser1, to_user=following)
            if following.id % 2 == 0:
                Friendship.objects.create(from_user=self.testuser2, to_user=following)

        url = FOLLOWINGS_URL.format(self.testuser1.id)
        self._test_friendship_pagination(url, page_size, max_page_size)

        # anonymous hasn't followed any users
        response = self.anonymous_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        response = self.testuser2_client.get(url, {'page': 1})
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

        response = self.testuser1_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], True)

    def _test_friendship_pagination(self, url, page_size, max_page_size):
        response = self.anonymous_client.get(url, {'page': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(len(response.data['results']), page_size)

        response = self.anonymous_client.get(url, {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['page_number'], 2)
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), page_size)

        response = self.anonymous_client.get(url, {'page': 3})
        self.assertEqual(response.status_code, 404)

        # test page size can not exceed max_page_size
        response = self.anonymous_client.get(url, {'page': 1, 'size': max_page_size + 1})
        self.assertEqual(len(response.data['results']), max_page_size)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)

        response = self.anonymous_client.get(url, {'page': 1, 'size': 2})
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['total_pages'], page_size)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)

