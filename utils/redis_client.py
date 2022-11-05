from django.conf import settings
import redis


class RedisClient:
    _conn = None

    @classmethod
    def get_connection(cls):
        # singleton pattern for each web request
        if cls._conn:
            return cls._conn
        cls._conn = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
        )

        return cls._conn

    @classmethod
    def clear(cls):
        # clear all keys in redis for testing purpose, we can't clear production redis
        if not settings.TESTING:
            raise Exception("You can not flush redis in production environment")
        conn = cls.get_connection()
        conn.flushdb()
