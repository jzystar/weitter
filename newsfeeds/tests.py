from gatekeeper.models import GateKeeper
from newsfeeds.services import NewsFeedServices
from newsfeeds.tasks import fanout_newsfeed_main_task
from testing.testcases import TestCase
from utils.redis_client import RedisClient
from weitter.cache import USER_NEWSFEEDS_PATTERN


class NewsFeedServiceTests(TestCase):

    def setUp(self):
        super(NewsFeedServiceTests, self).setUp()
        self.user1 = self.create_user('user1')
        self.user2 = self.create_user('user2')

    def test_get_user_newsfeeds(self):
        newsfeed_timestamps = []
        for i in range(3):
            weit = self.create_weit(self.user2)
            newsfeed = self.create_newsfeed(self.user1, weit)
            newsfeed_timestamps.append(newsfeed.created_at)
        newsfeed_timestamps = newsfeed_timestamps[::-1]

        # cache miss
        newsfeeds = NewsFeedServices.get_cached_newsfeeds(self.user1.id)
        self.assertEqual([f.created_at for f in newsfeeds], newsfeed_timestamps)

        # cache hit
        newsfeeds = NewsFeedServices.get_cached_newsfeeds(self.user1.id)
        self.assertEqual([f.created_at for f in newsfeeds], newsfeed_timestamps)

        # cache updated
        weit = self.create_weit(self.user1)
        new_newsfeed = self.create_newsfeed(self.user1, weit)
        newsfeeds = NewsFeedServices.get_cached_newsfeeds(self.user1.id)
        newsfeed_timestamps.insert(0, new_newsfeed.created_at)
        self.assertEqual([f.created_at for f in newsfeeds], newsfeed_timestamps)

    def test_create_new_newsfeed_before_get_cached_newsfeeds(self):
        feed1 = self.create_newsfeed(self.user1, self.create_weit(self.user1))
        self.clear_cache()
        conn = RedisClient.get_connection()

        key = USER_NEWSFEEDS_PATTERN.format(user_id=self.user1.id)
        self.assertEqual(conn.exists(key), False)
        feed2 = self.create_newsfeed(self.user1, self.create_weit(self.user1))
        self.assertEqual(conn.exists(key), True)

        feeds = NewsFeedServices.get_cached_newsfeeds(self.user1.id)
        self.assertEqual([f.created_at for f in feeds], [feed2.created_at, feed1.created_at])


class NewsFeedTaskTests(TestCase):

    def setUp(self):
        super(NewsFeedTaskTests, self).setUp()
        self.user1 = self.create_user('user1')
        self.user2 = self.create_user('user2')

    def test_fanout_main_task(self):
        weit = self.create_weit(self.user1, 'weit 1')
        if GateKeeper.is_switch_on('switch_newsfeed_to_hbase'):
            created_at = weit.timestamp
        else:
            created_at = weit.created_at

        self.create_friendship(self.user2, self.user1)
        msg = fanout_newsfeed_main_task(weit.id, created_at, self.user1.id)
        self.assertEqual(msg, '1 newsfeeds going to fanout, 1 batches created.')
        self.assertEqual(1 + 1, NewsFeedServices.count_all())
        cached_list = NewsFeedServices.get_cached_newsfeeds(self.user1.id)
        self.assertEqual(len(cached_list), 1)

        for i in range(2):
            user = self.create_user('someone{}'.format(i))
            self.create_friendship(user, self.user1)

        weit = self.create_weit(self.user1, 'weit 2')
        if GateKeeper.is_switch_on('switch_newsfeed_to_hbase'):
            created_at = weit.timestamp
        else:
            created_at = weit.created_at

        msg = fanout_newsfeed_main_task(weit.id, created_at, self.user1.id)
        self.assertEqual(msg, '3 newsfeeds going to fanout, 1 batches created.')
        self.assertEqual(4 + 2, NewsFeedServices.count_all())
        cached_list = NewsFeedServices.get_cached_newsfeeds(self.user1.id)
        self.assertEqual(len(cached_list), 2)

        user = self.create_user('another user')
        self.create_friendship(user, self.user1)
        weit = self.create_weit(self.user1, 'weit 3')
        if GateKeeper.is_switch_on('switch_newsfeed_to_hbase'):
            created_at = weit.timestamp
        else:
            created_at = weit.created_at

        msg = fanout_newsfeed_main_task(weit.id, created_at, self.user1.id)
        self.assertEqual(msg, '4 newsfeeds going to fanout, 2 batches created.')
        self.assertEqual(8 + 3, NewsFeedServices.count_all())
        cached_list = NewsFeedServices.get_cached_newsfeeds(self.user1.id)
        self.assertEqual(len(cached_list), 3)
        cached_list = NewsFeedServices.get_cached_newsfeeds(self.user2.id)
        self.assertEqual(len(cached_list), 3)
