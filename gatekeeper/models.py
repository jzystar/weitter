from utils.redis_client import RedisClient


class GateKeeper(object):

    @classmethod
    def get(cls, gk_name):
        """
        从redis中拿到对应gatekeeper的值
        """
        conn = RedisClient.get_connection()
        name = f'gatekeeper:{gk_name}'
        if not conn.exists(name):
            return {'percent': 0, 'description': ''}
        # redis 存的kv中v是一个dict，通过name 拿到这个dict的所有数据
        # 若hget(name, key)，是去name对应的dict中找到对应key的值
        redis_hash = conn.hgetall(name)
        return {
            'percent': int(redis_hash.get(b'percent', 0)),
            'description': str(redis_hash.get(b'description', 0)),
        }

    @classmethod
    def set_kv(cls, gk_name, key, value):
        conn = RedisClient.get_connection()
        name = f'gatekeeper:{gk_name}'
        conn.hset(name, key, value)

    @classmethod
    def turn_on(cls, gk_name):
        cls.set_kv(gk_name, 'percent', 100)

    @classmethod
    def is_switch_on(cls, gk_name):
        """
        percent为100才算switch on
        """
        return cls.get(gk_name)['percent'] == 100

    @classmethod
    def in_gk(cls, gk_name, user_id):
        """
        gatekeeper 漏斗判断
        针对user_id进行过滤，因为同一个用户每次访问的都需要是相同的版本，user_id取模的值永远不会改变
        """
        return user_id % 100 < cls.get(gk_name)['percent']
