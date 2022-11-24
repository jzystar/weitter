from django.conf import settings

import happybase


class HBaseClient:
    _conn = None

    @classmethod
    def get_connection(cls):
        # if cls._conn:
        #     return cls._conn
        cls._conn = happybase.Connection(settings.HBASE_HOST)
        return cls._conn

