from django.conf import settings
from utils.redis_serializers import DjangoModelSerializer
from utils.redis_client import RedisClient


class RedisHelper:

    @classmethod
    def _load_objects_to_cache(cls, key, objects):
        # cache miss 时，需要从数据库即queryset中取数据，存到cache中
        conn = RedisClient.get_connection()
        serialized_list = []
        # 最多只cache REDIS_LIST_LENGTH_LIMIT个数据，比如200个，超过这个的就去数据库里面读
        # 此时的数据量不会太大，所以可以直接访问数据库
        for obj in objects[: settings.REDIS_LIST_LENGTH_LIMIT]:
            serialized_data = DjangoModelSerializer.serialize(obj)
            serialized_list.append(serialized_data)

        if serialized_list:
            conn.rpush(key, *serialized_list)
            conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)

    @classmethod
    def load_objects(cls, key, queryset):
        conn = RedisClient.get_connection()

        # if cache hit, return it directly
        if conn.exists(key):
            serialized_list = conn.lrange(key, 0, -1)
            objects = []
            for serialized_data in serialized_list:
                deserialized_obj = DjangoModelSerializer.deserialize(serialized_data)
                objects.append(deserialized_obj)
            return objects

        # cache miss
        cls._load_objects_to_cache(key, queryset)
        # 与存在redis里面的数据统一，都是list, 因为cache hit时也返回的一个queryset list
        return list(queryset)

    @classmethod
    def push_object(cls, key, obj, queryset):
        conn = RedisClient.get_connection()
        if not conn.exists(key):
            cls._load_objects_to_cache(key, queryset)
            return
        serialized_data = DjangoModelSerializer.serialize(obj)
        conn.lpush(key, serialized_data)
        # redis 的区间是开区间，包括最后一个
        conn.ltrim(key, 0, settings.REDIS_LIST_LENGTH_LIMIT - 1)
