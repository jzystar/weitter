from friendships.api.paginations import FriendshipPagination
from friendships.models import Friendship
from friendships.services import FriendshipServices
from rest_framework.test import APIClient
from testing.testcases import TestCase
from utils.paginations import EndlessPagination

FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipApiTestCases(TestCase):

    def setUp(self):
        super(FriendshipApiTestCases, self).setUp()
        self.testuser1 = self.create_user('testuser1')
        self.testuser1_client = APIClient()
        self.testuser1_client.force_authenticate(self.testuser1)

        self.testuser2 = self.create_user('testuser2')
        self.testuser2_client = APIClient()
        self.testuser2_client.force_authenticate(self.testuser2)

        for i in range(2):
            follower = self.create_user('testuser2_follower{}'.format(i))
            self.create_friendship(from_user=follower, to_user=self.testuser2)

        for i in range(3):
            following = self.create_user('testuser2_following{}'.format(i))
            self.create_friendship(from_user=self.testuser2, to_user=following)

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

        before_count = FriendshipServices.get_following_count(self.testuser1.id)
        response = self.testuser1_client.post(FOLLOW_URL.format(self.testuser2.id))
        self.assertEqual(response.status_code, 201)
        after_count = FriendshipServices.get_following_count(self.testuser1.id)
        self.assertEqual(after_count, before_count + 1)

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
        self.create_friendship(from_user=self.testuser2, to_user=self.testuser1)
        before_count = FriendshipServices.get_following_count(self.testuser2.id)
        response = self.testuser2_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(FriendshipServices.get_following_count(self.testuser2.id), before_count - 1)

        # unfollow a nonfollowing user
        before_count = FriendshipServices.get_following_count(self.testuser2.id)
        response = self.testuser2_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(FriendshipServices.get_following_count(self.testuser2.id), before_count)

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
        page_size = EndlessPagination.page_size
        friendships = []
        for i in range(page_size * 2):
            follower = self.create_user('testuser1_follower{}'.format(i))
            friendship = self.create_friendship(from_user=follower, to_user=self.testuser1)
            friendships.append(friendship)
            if follower.id % 2 == 0:
                self.create_friendship(from_user=self.testuser2, to_user=follower)

        url = FOLLOWERS_URL.format(self.testuser1.id)
        self._paginate_until_the_end(url, 2, friendships)

        # anonymous hasn't followed any users
        response = self.anonymous_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        response = self.testuser2_client.get(url)
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)
    
    def test_followings_pagination(self):
        page_size = EndlessPagination.page_size
        friendships = []
        for i in range(page_size * 2):
            following = self.create_user('testuser1_following{}'.format(i))
            friendship = self.create_friendship(from_user=self.testuser1, to_user=following)
            friendships.append(friendship)
            if following.id % 2 == 0:
                self.create_friendship(from_user=self.testuser2, to_user=following)

        url = FOLLOWINGS_URL.format(self.testuser1.id)
        self._paginate_until_the_end(url, 2, friendships)

        # anonymous hasn't followed any users
        response = self.anonymous_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        response = self.testuser2_client.get(url)
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

        response = self.testuser1_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], True)

        # test pull new friendships
        last_created_at = friendships[-1].created_at
        response = self.testuser1_client.get(url, {'created_at__gt': last_created_at})
        self.assertEqual(response.status_code, 200)
        new_friends = [self.create_user('big_v{}'.format(i)) for i in range(3)]
        new_friendships = []
        for friend in new_friends:
            new_friendships.append(self.create_friendship(from_user=self.testuser1, to_user=friend))
        response = self.testuser1_client.get(url, {'created_at__gt': last_created_at})
        self.assertEqual(len(response.data['results']), 3)
        for result, friendship in zip(response.data['results'], reversed(new_friendships)):
            self.assertEqual(result['created_at'], friendship.created_at)

    def _paginate_until_the_end(self, url, expect_pages, friendships):
        results, pages = [], 0
        response = self.anonymous_client.get(url)
        results.extend(response.data['results'])
        pages += 1
        while response.data['has_next_page']:
            self.assertEqual(response.status_code, 200)
            last_item = response.data['results'][-1]
            response = self.anonymous_client.get(url, {
                'created_at__lt': last_item['created_at'],
            })
            results.extend(response.data['results'])
            pages += 1

        self.assertEqual(len(results), len(friendships))
        self.assertEqual(pages, expect_pages)
        # friendship is in ascending order, results is in descending order
        for result, friendship in zip(results, friendships[::-1]):
            self.assertEqual(result['created_at'], friendship.created_at)
