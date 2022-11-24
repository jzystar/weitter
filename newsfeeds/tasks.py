from celery import shared_task
from friendships.services import FriendshipServices
from newsfeeds.constants import FANOUT_BATCH_SIZE
from utils.loggers import logger
from utils.time_constants import OHE_HOUR
# from celery.utils.log import get_task_logger


@shared_task(routing_key='newsfeeds', time_limit=OHE_HOUR)
def fanout_newsfeed_batch_task(weit_id, created_at, follower_ids):
    # logger = get_task_logger(__name__)
    logger.info("Enter fanout_newsfeed_batch_task")

    from newsfeeds.services import NewsFeedServices
    # not allowed queries in for loop
    # for follower in followers:
    #     NewsFeed.objects.create(user=followers, weit=weit)

    batch_params = [
        {'weit_id': weit_id, 'user_id': follower_id, 'created_at': created_at}
        for follower_id in follower_ids
    ]

    # use bulk create
    newsfeeds = NewsFeedServices.batch_create(batch_params)

    return '{} newsfeeds created'.format(len(newsfeeds))


@shared_task(routing_key='default', time_limit=OHE_HOUR)
def fanout_newsfeed_main_task(weit_id, created_at, weit_user_id):
    # worker_logger = get_task_logger(__name__)
    logger.info("Enter fanout_newsfeed_main_task")
    from newsfeeds.services import NewsFeedServices

    # 将自己的刚发的weit排在最前面
    NewsFeedServices.create(user_id=weit_user_id, created_at=created_at, weit_id=weit_id)

    follower_ids = FriendshipServices.get_followers_id(weit_user_id)
    logger.info(f"Get user {weit_user_id} follower_ids {follower_ids}")

    index = 0
    while index < len(follower_ids):
        batch_follower_ids = follower_ids[index: index + FANOUT_BATCH_SIZE]
        fanout_newsfeed_batch_task.delay(weit_id, created_at, batch_follower_ids)
        index += FANOUT_BATCH_SIZE

    return '{} newsfeeds going to fanout, {} batches created.'.format(
        len(follower_ids),
        (len(follower_ids) - 1) // FANOUT_BATCH_SIZE + 1,
    )

