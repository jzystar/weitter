from newsfeeds.services import NewsFeedServices
from testing.testcases import TestCase
from utils.redis_client import RedisClient
from weitter.cache import USER_NEWSFEEDS_PATTERN
from newsfeeds.tasks import fanout_newsfeed_main_task
from newsfeeds.models import NewsFeed


class NewsFeedServiceTests(TestCase):

    def setUp(self):
        super(NewsFeedServiceTests, self).setUp()
        self.user1 = self.create_user('user1')
        self.user2 = self.create_user('user2')

    def test_get_user_newsfeeds(self):
        newsfeed_ids = []
        for i in range(3):
            weit = self.create_weit(self.user2)
            newsfeed = self.create_newsfeed(self.user1, weit)
            newsfeed_ids.append(newsfeed.id)
        newsfeed_ids = newsfeed_ids[::-1]

        # cache miss
        newsfeeds = NewsFeedServices.get_cached_newsfeeds(self.user1.id)
        self.assertEqual([f.id for f in newsfeeds], newsfeed_ids)

        # cache hit
        newsfeeds = NewsFeedServices.get_cached_newsfeeds(self.user1.id)
        self.assertEqual([f.id for f in newsfeeds], newsfeed_ids)

        # cache updated
        weit = self.create_weit(self.user1)
        new_newsfeed = self.create_newsfeed(self.user1, weit)
        newsfeeds = NewsFeedServices.get_cached_newsfeeds(self.user1.id)
        newsfeed_ids.insert(0, new_newsfeed.id)
        self.assertEqual([f.id for f in newsfeeds], newsfeed_ids)

    def test_create_new_newsfeed_before_get_cached_newsfeeds(self):
        feed1 = self.create_newsfeed(self.user1, self.create_weit(self.user1))

        RedisClient.clear()
        conn = RedisClient.get_connection()

        key = USER_NEWSFEEDS_PATTERN.format(user_id=self.user1.id)
        self.assertEqual(conn.exists(key), False)
        feed2 = self.create_newsfeed(self.user1, self.create_weit(self.user1))
        self.assertEqual(conn.exists(key), True)

        feeds = NewsFeedServices.get_cached_newsfeeds(self.user1.id)
        self.assertEqual([f.id for f in feeds], [feed2.id, feed1.id])


class NewsFeedTaskTests(TestCase):

    def setUp(self):
        super(NewsFeedTaskTests, self).setUp()
        self.user1 = self.create_user('user1')
        self.user2 = self.create_user('user2')

    def test_fanout_main_task(self):
        weit = self.create_weit(self.user1, 'weit 1')
        self.create_friendship(self.user2, self.user1)
        msg = fanout_newsfeed_main_task(weit.id, self.user1.id)
        self.assertEqual(msg, '1 newsfeeds going to fanout, 1 batches created.')
        self.assertEqual(1 + 1, NewsFeed.objects.count())
        cached_list = NewsFeedServices.get_cached_newsfeeds(self.user1.id)
        self.assertEqual(len(cached_list), 1)

        for i in range(2):
            user = self.create_user('someone{}'.format(i))
            self.create_friendship(user, self.user1)
        weit = self.create_weit(self.user1, 'weit 2')
        msg = fanout_newsfeed_main_task(weit.id, self.user1.id)
        self.assertEqual(msg, '3 newsfeeds going to fanout, 1 batches created.')
        self.assertEqual(4 + 2, NewsFeed.objects.count())
        cached_list = NewsFeedServices.get_cached_newsfeeds(self.user1.id)
        self.assertEqual(len(cached_list), 2)

        user = self.create_user('another user')
        self.create_friendship(user, self.user1)
        weit = self.create_weit(self.user1, 'weit 3')
        msg = fanout_newsfeed_main_task(weit.id, self.user1.id)
        self.assertEqual(msg, '4 newsfeeds going to fanout, 2 batches created.')
        self.assertEqual(8 + 3, NewsFeed.objects.count())
        cached_list = NewsFeedServices.get_cached_newsfeeds(self.user1.id)
        self.assertEqual(len(cached_list), 3)
        cached_list = NewsFeedServices.get_cached_newsfeeds(self.user2.id)
        self.assertEqual(len(cached_list), 3)
