from testing.testcases import TestCase
from rest_framework.test import APIClient
from newsfeeds.models import NewsFeed
from utils.paginations import EndlessPagination
from django.conf import settings
from newsfeeds.services import NewsFeedServices


NEWSFEED_URL = '/api/newsfeeds/'
FOLLOW_URL = '/api/friendships/{}/follow/'
POST_WEITS_URL = '/api/weits/'

class NewsFeedApiTests(TestCase):

    def setUp(self):
        self.clear_cache()
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

    def test_user_cache(self):
        profile = self.user2.profile
        profile.nickname = 'user2nickname'
        profile.save()

        self.assertEqual(self.user1.username, 'user1')
        self.create_newsfeed(self.user2, self.create_weit(self.user1))
        self.create_newsfeed(self.user2, self.create_weit(self.user2))

        response = self.user2_client.get(NEWSFEED_URL)
        results = response.data['results']
        self.assertEqual(results[0]['weit']['user']['username'], 'user2')
        self.assertEqual(results[0]['weit']['user']['nickname'], 'user2nickname')
        self.assertEqual(results[1]['weit']['user']['username'], 'user1')

        self.user1.username = 'user1username'
        self.user1.save()
        profile.nickname = 'user2newnickname'
        profile.save()

        response = self.user2_client.get(NEWSFEED_URL)
        results = response.data['results']
        self.assertEqual(results[0]['weit']['user']['username'], 'user2')
        self.assertEqual(results[0]['weit']['user']['nickname'], 'user2newnickname')
        self.assertEqual(results[1]['weit']['user']['username'], 'user1username')

    def test_weit_cache(self):
        weit = self.create_weit(self.user1, 'content1')
        self.create_newsfeed(self.user2, weit)
        response = self.user2_client.get(NEWSFEED_URL)
        results = response.data['results']
        self.assertEqual(results[0]['weit']['user']['username'], 'user1')
        self.assertEqual(results[0]['weit']['content'], 'content1')

        # update username
        self.user1.username = 'newuser1'
        self.user1.save()
        response = self.user2_client.get(NEWSFEED_URL)
        results = response.data['results']
        self.assertEqual(results[0]['weit']['user']['username'], 'newuser1')

        # update content
        weit.content='newcontent1'
        weit.save()
        response = self.user2_client.get(NEWSFEED_URL)
        results = response.data['results']
        self.assertEqual(results[0]['weit']['content'], 'newcontent1')

    def _paginate_to_get_newsfeeds(self, client):
        # paginate until the end
        response = client.get(NEWSFEED_URL)
        results = response.data['results']
        while response.data['has_next_page']:
            created_at__lt = response.data['results'][-1]['created_at']
            response = client.get(NEWSFEED_URL, {'created_at__lt': created_at__lt})
            results.extend(response.data['results'])
        return results

    def test_redis_list_limit(self):
        list_limit = settings.REDIS_LIST_LENGTH_LIMIT
        page_size = 20
        users = [self.create_user('testuser{}'.format(i)) for i in range(5)]
        newsfeeds = []
        for i in range(list_limit + page_size):
            weit = self.create_weit(user=users[i % 5], content='feed{}'.format(i))
            feed = self.create_newsfeed(self.user1, weit)
            newsfeeds.append(feed)
        newsfeeds = newsfeeds[::-1]

        # only cached list_limit objects
        cached_newsfeeds = NewsFeedServices.get_cached_newsfeeds(self.user1.id)
        self.assertEqual(len(cached_newsfeeds), list_limit)
        queryset = NewsFeed.objects.filter(user=self.user1)
        self.assertEqual(queryset.count(), list_limit + page_size)

        results = self._paginate_to_get_newsfeeds(self.user1_client)
        self.assertEqual(len(results), list_limit + page_size)
        for i in range(list_limit + page_size):
            self.assertEqual(newsfeeds[i].id, results[i]['id'])

        # a followed user create a new weit
        self.create_friendship(self.user1, self.user2)
        new_weit = self.create_weit(self.user2, 'a new weit')
        NewsFeedServices.fanout_to_followers(new_weit)

        def _test_newsfeeds_after_new_feed_pushed():
            results = self._paginate_to_get_newsfeeds(self.user1_client)
            self.assertEqual(len(results), list_limit + page_size + 1)
            self.assertEqual(results[0]['weit']['id'], new_weit.id)
            for i in range(list_limit + page_size):
                self.assertEqual(newsfeeds[i].id, results[i + 1]['id'])

        _test_newsfeeds_after_new_feed_pushed()

        # cache expired
        self.clear_cache()
        _test_newsfeeds_after_new_feed_pushed()



