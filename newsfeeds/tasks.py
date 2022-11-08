from celery import shared_task
from friendships.services import FriendshipServices
from newsfeeds.models import NewsFeed
from utils.time_constants import OHE_HOUR
from weits.models import Weit


@shared_task(time_limit=OHE_HOUR)
def fanout_newsfeed_task(weit_id):
    from newsfeeds.services import NewsFeedServices

    weit = Weit.objects.get(id=weit_id)
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
        NewsFeedServices.push_newsfeed_to_cache(newsfeed)
