from testing.testcases import TestCase
from rest_framework.test import APIClient
from newsfeeds.models import NewsFeed
from utils.paginations import EndlessPagination


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
        self.assertEqual(len(response.data['results']), 0)
        # user1 post a weit
        self.user1_client.post(POST_WEITS_URL, {'content': 'hello word!'})
        response = self.user1_client.get(NEWSFEED_URL)
        self.assertEqual(len(response.data['results']), 1)

        # follow others to see following's weits
        self.user1_client.post(FOLLOW_URL.format(self.user2.id))
        response = self.user2_client.post(POST_WEITS_URL, {'content': 'Weit from user2'})
        weit_id = response.data['id']
        response = self.user1_client.get(NEWSFEED_URL)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['weit']['id'], weit_id)

    def test_pagination(self):
        page_size = EndlessPagination.page_size
        followed_user = self.create_user('followed')
        # create page_size * 2 weits
        newsfeeds = []
        for i in range(page_size * 2):
            weit = self.create_weit(followed_user, 'weit{}'.format(i))
            newsfeed = self.create_newsfeed(user=self.user1, weit=weit)
            newsfeeds.append(newsfeed)

        newsfeeds = newsfeeds[::-1]

        # pull the first page
        response = self.user1_client.get(NEWSFEED_URL)
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], newsfeeds[0].id)
        self.assertEqual(response.data['results'][1]['id'], newsfeeds[1].id)
        self.assertEqual(response.data['results'][page_size - 1]['id'], newsfeeds[page_size - 1].id)

        # pull the second page
        response = self.user1_client.get(NEWSFEED_URL, {
            'created_at__lt': newsfeeds[page_size - 1].created_at,
        })
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], newsfeeds[page_size].id)
        self.assertEqual(response.data['results'][1]['id'], newsfeeds[page_size + 1].id)
        self.assertEqual(response.data['results'][page_size - 1]['id'], newsfeeds[2 * page_size - 1].id)

        # pull latest newsfeed
        response = self.user1_client.get(NEWSFEED_URL, {
            'user_id': self.user1.id,
            'created_at__gt': newsfeeds[0].created_at,
        })

        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 0)

        new_weit = self.create_weit(followed_user, 'a new weit comes in')
        new_newsfeed = self.create_newsfeed(self.user1, new_weit)
        response = self.user1_client.get(NEWSFEED_URL, {
            'created_at__gt': newsfeeds[0].created_at,
        })

        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], new_newsfeed.id)


