from django.conf import settings
from django.core.cache import caches
from friendships.models import Friendship
from gatekeeper.models import GateKeeper
from friendships.hbase_models import HBaseFollowing, HBaseFollower
from weitter.cache import FOLLOWINGS_PATTERN
import time

cache = caches['testing'] if settings.TESTING else caches['default']


class FriendshipServices(object):

    @classmethod
    def get_followers(cls, user):
        # following not good because in return lines, query will be run multiple times to get each from_user
        # friendships = Friendship.objects.filter(to_user=user)
        # return [friendship.from_user for friendship in friendships]

        # friendships = Friendship.objects.filter(to_user=user)
        # friendships_ids = [friendship.from_user_id for friendship in friendships]
        # return User.objects.filter(id__in=friendships_ids)

        # from_user_ids = Friendship.objects.filter(to_user=user).values_list('from_user_id', flat=True)
        # return User.objects.filter(id__in=from_user_ids)

        friendships = Friendship.objects.filter(to_user=user).prefetch_related('from_user')
        return [friendship.from_user for friendship in friendships]

    @classmethod
    def get_followers_id(cls, user_id):
        friendships = Friendship.objects.filter(to_user_id=user_id)
        return [friendship.from_user_id for friendship in friendships]

    @classmethod
    def get_following_user_id_set(cls, from_user_id):
        key = FOLLOWINGS_PATTERN.format(user_id=from_user_id)
        user_id_set = cache.get(key)
        if user_id_set is not None:
            return user_id_set
        friendships = Friendship.objects.filter(from_user_id=from_user_id)
        user_id_set = set([
            fs.to_user_id for fs in friendships
        ])
        cache.set(key, user_id_set)
        return user_id_set

    @classmethod
    def invalidate_following_cache(cls, from_user_id):
        key = FOLLOWINGS_PATTERN.format(user_id=from_user_id)
        cache.delete(key)

    @classmethod
    def follow(cls, from_user_id, to_user_id):
        if from_user_id == to_user_id:
            return None

        if not GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            # create data in mysql
            return Friendship.objects.create(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
            )

        # create data in hbase
        now = int(time.time() * 1000000)
        HBaseFollower.create(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            created_at=now,
        )
        # 在两张表中分别创建，因为数据相同，所以选择一个返回即可。
        return HBaseFollowing.create(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            created_at=now,
        )

