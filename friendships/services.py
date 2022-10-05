from friendships.models import Friendship
class FriendshipServices(object):

    @classmethod
    def get_followers(self, user):
        # following not good because in return lines, query will be run multiple times to get each from_user
        # friendships = Friendship.objects.filter(to_user=user)
        # return [friendship.from_user for friendship in friendships]

        # friendships = Friendship.objects.filter(to_user=user)
        # friendships_ids = [friendship.from_user_id for friendship in friendships]
        # return User.objects.filter(id__in=friendships_ids)
        friendships = Friendship.objects.filter(to_user=user).prefetch_related('from_user')
        return [friendship.from_user for friendship in friendships]

