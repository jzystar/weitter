from django.conf import settings
from django_hbase.models import HBaseModel
from utils.loggers import logger
from utils.redis_client import RedisClient
from utils.redis_serializers import DjangoModelSerializer, HBaseModelSerializer


class RedisHelper:

    @classmethod
    def _load_objects_to_cache(cls, key, objects, serializer):
        # cache miss 时，需要从数据库即queryset中取数据，存到cache中
        conn = RedisClient.get_connection()
        serialized_list = []
        logger.info(f"Cache miss and load objects data {objects} to redis")
        for obj in objects:
            serialized_data = serializer.serialize(obj)
            serialized_list.append(serialized_data)

        logger.info(f"Serialized list data {serialized_list} are loading to redis")
        if serialized_list:
            conn.rpush(key, *serialized_list)
            conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)

    @classmethod
    def load_objects(cls, key, lazy_load_objects, serializer=DjangoModelSerializer):
        # 最多只cache REDIS_LIST_LENGTH_LIMIT个数据，比如200个，超过这个的就去数据库里面读
        # 此时的数据量不会太大，所以可以直接访问数据库

        conn = RedisClient.get_connection()
        # if cache hit, return it directly
        if conn.exists(key):
            serialized_list = conn.lrange(key, 0, -1)
            logger.info(f'Get key:{key} from redis: {serialized_list}')
            objects = []
            for serialized_data in serialized_list:
                deserialized_obj = serializer.deserialize(serialized_data)
                objects.append(deserialized_obj)
            logger.info(f'Cache return deserialized {objects}')
            return objects

        # cache miss
        logger.info(f'Get key:{key} missing!')
        objects = lazy_load_objects(settings.REDIS_LIST_LENGTH_LIMIT)
        cls._load_objects_to_cache(key, objects, serializer)
        # 与存在redis里面的数据统一，都是list, 因为cache hit时也返回的一个queryset list
        return list(objects)

    @classmethod
    def push_object(cls, key, obj, lazy_load_objects):
        if isinstance(obj, HBaseModel):
            logger.info(f'Push hbase model with key:{key}, data: {obj}')
            serializer = HBaseModelSerializer
        else:
            logger.info(f'Push mysql model with key:{key}, data: {obj}')
            serializer = DjangoModelSerializer
        conn = RedisClient.get_connection()
        if not conn.exists(key):
            logger.info(f'Cache miss for key {key}')
            objects = lazy_load_objects(settings.REDIS_LIST_LENGTH_LIMIT)
            cls._load_objects_to_cache(key, objects, serializer)
            return

        serialized_data = serializer.serialize(obj)
        logger.info(f'Push serialized data {serialized_data} to redis list key {key}')
        conn.lpush(key, serialized_data)
        # redis 的区间是开区间，包括最后一个
        conn.ltrim(key, 0, settings.REDIS_LIST_LENGTH_LIMIT - 1)

    @classmethod
    def get_count_key(cls, obj, attr):
        return '{}.{}:{}'.format(obj.__class__.__name__, attr, obj.id)

    @classmethod
    def incr_count(cls, obj, attr):
        conn = RedisClient.get_connection()
        key = cls.get_count_key(obj, attr)
        if conn.exists(key):
            return conn.incr(key)

        # back fill cache from db
        # 不执行+1操作，因为必须保证调用incr_count之前，数据库层面obj.attr已经+1了
        obj.refresh_from_db()
        conn.set(key, getattr(obj, attr))
        conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)
        return getattr(obj, attr)

    @classmethod
    def decr_count(cls, obj, attr):
        conn = RedisClient.get_connection()
        key = cls.get_count_key(obj, attr)
        if conn.exists(key):
            return conn.decr(key)
        # 不执行-1操作，因为必须保证调用incr_count之前，数据库层面obj.attr已经-1了
        # 从这里我们也能看出，每次更新cache时，若cache不在，则直接去数据库里面取，此时无须更改，因为数据库已经是最新的
        # 若cache存在，则针对cache进行更新改动
        obj.refresh_from_db()
        conn.set(key, getattr(obj, attr))
        conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)
        return getattr(obj, attr)

    @classmethod
    def get_count(cls, obj, attr):
        conn = RedisClient.get_connection()
        key = cls.get_count_key(obj, attr)
        count = conn.get(key)
        if count is not None:
            return int(count)

        obj.refresh_from_db()
        count = getattr(obj, attr)
        conn.set(key, count)
        return count


