from gatekeeper.models import GateKeeper
from newsfeeds.models import NewsFeed, HBaseNewsFeed
from newsfeeds.tasks import fanout_newsfeed_main_task
from utils.loggers import logger
from utils.redis_helper import RedisHelper
from utils.redis_serializers import HBaseModelSerializer, DjangoModelSerializer
from weits.models import Weit
from weitter.cache import USER_NEWSFEEDS_PATTERN


def lazy_load_newsfeeds(user_id):
    # 因为queryset是懒惰加载，所以这里模仿django对于mysql的queryset，对hbase 的filter操作进行懒惰加载
    # 调用时传递这个函数，lazy_load_func = lazy_load_newsfeeds(user_id=1)此时返回一个函数对象，具体内容并未执行
    def _lazy_load(limit):
        if GateKeeper.is_switch_on('switch_newsfeed_to_hbase'):
            # 此时直接访问hbase取数据了
            return HBaseNewsFeed.filter(prefix=(user_id,), limit=limit, reverse=True)
        # 此时对于queryset取分片了，所以会执行filter
        return NewsFeed.objects.filter(user_id=user_id).order_by('-created_at')[:limit]
    # 返回函数对象，此时_lazy_load并未真正执行，所以其中的对于数据库的访问页还没执行，用于懒惰加载
    return _lazy_load


class NewsFeedServices(object):

    # 对于明星，粉丝很多，比如超过1kw的，每个weit都会fanout给所有的followers，这样会有很大空间和时间开销
    # 所以对于明星用户来讲，还是尽量用pull的机制来做，
    @classmethod
    def fanout_to_followers(cls, weit: Weit):
        # 在celery配置的message queue中创建一个fanout任务，参数是weit.id，任意一个监听message queue的worker进程都有机会拿到这个任务
        # worker进程中会执行fanout_newsfeed_task的代码实现一个异步的任务处理，不影响当前web的操作
        # delay里的参数必须是可以背celery serialize的值，因为worker进程是一个独立进程，甚至在不同机器上，没有办法知道当前web进程
        # 的内存空间里的值是什么，所以我们只把weit.id作为参数传进去，而不能把weit直接传进去，因为celery并不知道如何serialize Weit

        # 无delay是同步任务
        # fanout_newsfeed_task(weit.id)
        # 加delay为异步任务, testing 时由于配置过了，会不用delay直接同步执行
        logger.info('weit_id:{}, timestamp:{}, user_id:{}'.format(weit.id, weit.timestamp, weit.user_id))
        fanout_newsfeed_main_task.delay(weit.id, weit.timestamp, weit.user_id)

    @classmethod
    def get_cached_newsfeeds(cls, user_id):
        # queryset lazy loading
        if GateKeeper.is_switch_on('switch_newsfeed_to_hbase'):
            serializer = HBaseModelSerializer
        else:
            serializer = DjangoModelSerializer
        key = USER_NEWSFEEDS_PATTERN.format(user_id=user_id)
        return RedisHelper.load_objects(key, lazy_load_newsfeeds(user_id), serializer=serializer)

    @classmethod
    def push_newsfeed_to_cache(cls, newsfeed):
        key = USER_NEWSFEEDS_PATTERN.format(user_id=newsfeed.user_id)
        RedisHelper.push_object(key, newsfeed, lazy_load_newsfeeds(newsfeed.user_id))

    @classmethod
    def create(cls, **kwargs):
        logger.info("Enter newsfeed create")
        if GateKeeper.is_switch_on('switch_newsfeed_to_hbase'):
            logger.info("HBaseNewsFeed create")
            newsfeed = HBaseNewsFeed.create(**kwargs)
            # push to cache as there's no listener on hbase create
            cls.push_newsfeed_to_cache(newsfeed)
        else:
            del kwargs['created_at']
            logger.info(f'kwargs are {kwargs}')
            newsfeed = NewsFeed.objects.create(**kwargs)
        return newsfeed

    @classmethod
    def batch_create(cls, batch_params):
        if GateKeeper.is_switch_on('switch_newsfeed_to_hbase'):
            newsfeeds = HBaseNewsFeed.batch_create(batch_params)
            # push to cache as there's no listener on hbase create
        else:
            newsfeeds = [NewsFeed(**params) for params in batch_params]
            NewsFeed.objects.bulk_create(newsfeeds)

        # bulk create will not trigger post_save signal, we need write code to do this
        for newsfeed in newsfeeds:
            cls.push_newsfeed_to_cache(newsfeed)
        return newsfeeds

    @classmethod
    def count(cls, user_id=None):
        # for unit test only
        if GateKeeper.is_switch_on('switch_newsfeed_to_hbase'):
            return len(HBaseNewsFeed.filter(prefix=(user_id, )))
        else:
            return NewsFeed.objects.filter(user_id=user_id).count()

    @classmethod
    def count_all(cls):
        # for unit test only
        if GateKeeper.is_switch_on('switch_newsfeed_to_hbase'):
            return len(HBaseNewsFeed.filter())
        else:
            return NewsFeed.objects.count()
