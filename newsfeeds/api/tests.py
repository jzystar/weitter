from testing.testcases import TestCase
from rest_framework.test import APIClient
from newsfeeds.models import NewsFeed


NEWSFEED_URL = '/api/newsfeeds/'
FOLLOW_URL = '/api/friendships/{}/follow/'
POST_WEITS_URL = '/api/weits/'

class NewsFeedApiTests(TestCase):

    def setUp(self):
        self.user1 = self.create_user('user1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('user2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

    def test_list(self):
        # login
        response = self.anonymous_client.get(NEWSFEED_URL)
        self.assertEqual(response.status_code, 403)
        # post method
        response = self.user1_client.post(NEWSFEED_URL)
        self.assertEqual(response.status_code, 405)
        # get 0 weits
        response = self.user1_client.get(NEWSFEED_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['newsfeeds']), 0)
        # user1 post a weit
        self.user1_client.post(POST_WEITS_URL, {'content': 'hello word!'})
        response = self.user1_client.get(NEWSFEED_URL)
        self.assertEqual(len(response.data['newsfeeds']), 1)

        # follow others to see following's weits
        self.user1_client.post(FOLLOW_URL.format(self.user2.id))
        response = self.user2_client.post(POST_WEITS_URL, {'content': 'Weit from user2'})
        weit_id = response.data['id']
        response = self.user1_client.get(NEWSFEED_URL)
        self.assertEqual(len(response.data['newsfeeds']), 2)
        self.assertEqual(response.data['newsfeeds'][0]['weit']['id'], weit_id)
