from newsfeeds.models import NewsFeed
from newsfeeds.tasks import fanout_newsfeed_task
from utils.redis_helper import RedisHelper
from weitter.cache import USER_NEWSFEEDS_PATTERN


class NewsFeedServices(object):

    # 对于明星，粉丝很多，比如超过1kw的，每个weit都会fanout给所有的followers，这样会有很大空间和时间开销
    # 所以对于明星用户来讲，还是尽量用pull的机制来做，
    @classmethod
    def fanout_to_followers(cls, weit):
        # 在celery配置的message queue中创建一个fanout任务，参数是weit.id，任意一个监听message queue的worker进程都有机会拿到这个任务
        # worker进程中会执行fanout_newsfeed_task的代码实现一个异步的任务处理，不影响当前web的操作
        # delay里的参数必须是可以背celery serialize的值，因为worker进程是一个独立进程，甚至在不同机器上，没有办法知道当前web进程
        # 的内存空间里的值是什么，所以我们只把weit.id作为参数传进去，而不能把weit直接传进去，因为celery并不知道如何serialize Weit

        # 无delay是同步任务
        # fanout_newsfeed_task(weit.id)
        # 加delay为异步任务, testing 时由于配置过了，会不用delay直接同步执行
        fanout_newsfeed_task.delay(weit.id)

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

