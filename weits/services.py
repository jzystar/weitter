from weits.models import Weit, WeitPhoto
from weitter.cache import USER_WEITS_PATTERN
from utils.redis_helper import RedisHelper


class WeitService(object):

    @classmethod
    def create_photos_from_files(cls, weit, files):
        photos = []
        for index, file in enumerate(files):
            photo = WeitPhoto(
                weit=weit,
                user=weit.user,
                file=file,
                order=index,
            )
            photos.append(photo)
        WeitPhoto.objects.bulk_create(photos)

    @classmethod
    def get_cached_weits(cls, user_id):
        # queryset lazy loading, so we don't execute sql when we define the queryset
        queryset = Weit.objects.filter(user_id=user_id).order_by('-created_at')
        key = USER_WEITS_PATTERN.format(user_id=user_id)
        return RedisHelper.load_objects(key, queryset)

    @classmethod
    def push_weit_to_cache(cls, weit):
        queryset = Weit.objects.filter(user_id=weit.user_id).order_by('-created_at')
        key = USER_WEITS_PATTERN.format(user_id=weit.user_id)
        RedisHelper.push_object(key, weit, queryset)



