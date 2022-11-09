from celery import shared_task
from friendships.services import FriendshipServices
from newsfeeds.models import NewsFeed
from utils.time_constants import OHE_HOUR
from weits.models import Weit
from newsfeeds.constants import FANOUT_BATCH_SIZE


@shared_task(routing_key='newsfeeds', time_limit=OHE_HOUR)
def fanout_newsfeed_batch_task(weit_id, follower_ids):
    from newsfeeds.services import NewsFeedServices
    # not allowed queries in for loop
    # for follower in followers:
    #     NewsFeed.objects.create(user=followers, weit=weit)

    # use bulk create
    newsfeeds = [
        NewsFeed(user_id=follower_id, weit_id=weit_id)
        for follower_id in follower_ids
    ]
    NewsFeed.objects.bulk_create(newsfeeds)

    # bulk create will not trigger post_save signal, we need write code to do this
    for newsfeed in newsfeeds:
        NewsFeedServices.push_newsfeed_to_cache(newsfeed)

    return '{} newsfeeds created'.format(len(newsfeeds))


@shared_task(routing_key='default', time_limit=OHE_HOUR)
def fanout_newsfeed_main_task(weit_id, weit_user_id):
    # 将自己的刚发的weit排在最前面
    NewsFeed.objects.create(user_id=weit_user_id, weit_id=weit_id)

    follower_ids = FriendshipServices.get_followers_id(weit_user_id)
    index = 0
    while index < len(follower_ids):
        batch_follower_ids = follower_ids[index: index + FANOUT_BATCH_SIZE]
        fanout_newsfeed_batch_task.delay(weit_id, batch_follower_ids)
        index += FANOUT_BATCH_SIZE

    return '{} newsfeeds going to fanout, {} batches created.'.format(
        len(follower_ids),
        (len(follower_ids) - 1) // FANOUT_BATCH_SIZE + 1,
    )

