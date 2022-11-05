from friendships.services import FriendshipServices
from newsfeeds.models import NewsFeed
from weitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis_helper import RedisHelper


class NewsFeedServices(object):

    # 对于明星，粉丝很多，比如超过1kw的，每个weit都会fanout给所有的followers，这样会有很大空间和时间开销
    # 所以对于明星用户来讲，还是尽量用pull的机制来做，
    @classmethod
    def fanout_to_followers(cls, weit):
        followers = FriendshipServices.get_followers(weit.user)
        # not allowed queries in for loop
        # for follower in followers:
        #     NewsFeed.objects.create(user=followers, weit=weit)

        # use bulk create
        newsfeeds = [
            NewsFeed(user=follower, weit=weit)
            for follower in followers
        ]
        newsfeeds.append(NewsFeed(user=weit.user, weit=weit))
        NewsFeed.objects.bulk_create(newsfeeds)

        # bulk create will not trigger post_save signal, we need write code to do this
        for newsfeed in newsfeeds:
            cls.push_newsfeed_to_cache(newsfeed)

    @classmethod
    def get_cached_newsfeeds(cls, user_id):
        # queryset lazy loading
        queryset = NewsFeed.objects.filter(user_id=user_id).order_by('-created_at')
        key = USER_NEWSFEEDS_PATTERN.format(user_id=user_id)
        return RedisHelper.load_objects(key, queryset)

    @classmethod
    def push_newsfeed_to_cache(cls, newsfeed):
        queryset = NewsFeed.objects.filter(user_id=newsfeed.user_id).order_by('-created_at')
        key = USER_NEWSFEEDS_PATTERN.format(user_id=newsfeed.user_id)
        RedisHelper.push_object(key, newsfeed, queryset)

