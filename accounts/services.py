from accounts.models import UserProfile
from django.conf import settings
from django.core.cache import caches
from utils.memcached_helper import MemcachedHelper
from weitter.cache import USER_PROFILE_PATTERN
from django.contrib.auth.models import User

cache = caches['testing'] if settings.TESTING else caches['default']


class UserService:

    @classmethod
    def get_profile_through_cache(cls, user_id):
        key = USER_PROFILE_PATTERN.format(user_id=user_id)

        profile = cache.get(key)
        if profile is not None:
            return profile

        # cache miss, read from db
        profile, _ = UserProfile.objects.get_or_create(user_id=user_id)
        cache.set(key, profile)
        return profile

    @classmethod
    def invalidate_profile(cls, user_id):
        key = USER_PROFILE_PATTERN.format(user_id=user_id)
        cache.delete(key)

    @classmethod
    def get_user_by_id(cls, user_id):
        return MemcachedHelper.get_object_through_cache(User, user_id)

