from friendships.services import FriendshipServices
from newsfeeds.models import NewsFeed
class NewsFeedServices(object):

    @classmethod
    def fanout_to_followers(self, weit):
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
