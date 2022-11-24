from .exceptions import EmptyColumnError, BadRowKeyError
from .fields import HBaseField, IntegerField, TimestampField
from django.conf import settings
from django_hbase.client import HBaseClient
from utils.loggers import logger


# 需要理解透cls，self 即类和实例之间区别，万物皆对象，cls和self是不同的对象，那么类属性和实例的属性则是分开的,
# 这里可以把cls和self当成不同实例，cls用来取Field对应的名称和类型，self用来给Field对应名称来赋一个新值
# 也需要理解__dict__中变量名和值的映射
# 重要：目前版本，传入happybase的参数字符串不需要encode成bytes了（比如row_key，value等），但是从hbase读取到的值还是bytes，注意转换成相应类型
class HBaseModel:
    class Meta:
        row_key = ()
        table_name = None

    def __init__(self, **kwargs):
        """
        实例化，需要对类属性的所有field进行赋值操作，来生成实例化的对象的对应属性
        实例化对象的属性名称与类属性名相同，值是具体的值，比如整数或者字符串等，而HbaseModel类属性的值是HBaseField实例
        所以在init中要对实例化对象进行对应属性的赋值操作
        field_name表示类/实例对象中的HBaseField类型属性名称，
        field_value或者value表示对象属性field的值，
        field_type表示类属性field的值，即HBaseField的实例
        """
        field_maps = self.get_field_maps()
        for field_name in field_maps.keys():
            setattr(self, field_name, kwargs.get(field_name))

    @classmethod
    def get_field_maps(cls):
        """
        获取HbaseModel类中所有的field，
        return dict，key是field名称，value是field类型对应实例
        """
        field_maps = dict()
        for field_name, field_type in cls.__dict__.items():
            if isinstance(field_type, HBaseField):
                field_maps[field_name] = field_type
        return field_maps

    @classmethod
    def serialize_field(cls, field_type, value):
        """
        序列化单个字段field为字符串
        int类型不足16位前置补0
        需要反转的字段进行反转
        """
        value = str(value)
        if isinstance(field_type, IntegerField):
            while len(value) < 16:
                value = '0' + value
        if field_type.reverse:
            value = value[::-1]
        return value

    @classmethod
    def deserialize_field(cls, field_name, field_value):
        """
        针对field的字符串值进行反序列化
        """
        #field_value = column_value.decode('utf-8')
        field_type = cls.get_field_maps()[field_name]
        if field_type.reverse:
            field_value = field_value[::-1]
        if field_type.field_type in [IntegerField.field_type, TimestampField.field_type]:
            return int(field_value)
        return field_value

    @classmethod
    def serialize_row_key(cls, data, is_prefix=False):
        """
        序列化row key成为字节格式，先转变为string，再encode到bytes
        序列化格式为，多个属性的值用冒号:分割
        is_prefix 为True则只serialize row_key的前缀部分然后跳出循环，不需要对所有row_key组成部分serialize
        {key1: val1} -> b"val1"
        {key1: val1, key2: val2} -> b"val1:val2"
        """
        if not cls.Meta.row_key:
            raise BadRowKeyError('Missing row key in Hbase Meta class')
        row_key_values = []
        field_maps = cls.get_field_maps()
        for key in cls.Meta.row_key:
            value = data.get(key)
            if not value:
                if not is_prefix:
                    raise BadRowKeyError(f'{key} is missing in row key of {cls.__name__}')
                # 若是前缀的话，遇到空的部分直接跳出返回
                break
            field_type = field_maps.get(key)
            value = cls.serialize_field(field_type, value)
            # 对于连接符":"的判断放到serialize_field_value() 中去？
            if ':' in value:
                raise BadRowKeyError(f'{key} should not contain ":" in its serialized value {value}')
            row_key_values.append(value)
        return bytes(':'.join(row_key_values), encoding='utf-8')

    @classmethod
    def deserialize_row_key(cls, row_key):
        """
        "val1" -> {'key1':va1, 'key2': None, 'key3': None}
        "val1:val2" -> {'key1':va1, 'key2': val2, 'key3': None}
        "val1:val2:val3" -> {'key1':va1, 'key2': val2, 'key3': val3}
        若row_key不是二进制字节，可以直接处理字符串格式，否则进行转换
        """
        if isinstance(row_key, bytes):
            row_key = row_key.decode('utf-8')
        field_data_maps = dict()
        field_values = row_key.split(':')
        index = 0
        for field_name in cls.Meta.row_key:
            if index >= len(field_values):
                break
            field_data_maps[field_name] = cls.deserialize_field(field_name, field_values[index])
            index += 1
        return field_data_maps

    @classmethod
    def serialize_row_data(cls, data):
        """
        序列化每行中的列的值
        返回dict，key为column_family:column_qualifier进行列簇和列进行连接，value为对应的最新版本的值, 且要进行field序列化
        """
        row_data = {}
        field_maps = cls.get_field_maps()
        for field_name, field_type in field_maps.items():
            if field_type.column_family:
                column_key = "{}:{}".format(field_type.column_family, field_name)
                value = data.get(field_name)
                if value is not None:
                    row_data[column_key] = cls.serialize_field(field_type, value)
        return row_data

    @property
    def row_key(self):
        """
        属性方法，将row key视作一个属性
        """
        return self.serialize_row_key(self.__dict__)

    @classmethod
    def init_from_row(cls, row_key, row_data):
        """
        把HBase中存储的row_key，row_data的格式转化为HbaseModel的实例对象，算是一个对于row_key和row_data两部分的反序列化
        其中从api拿到的rowkey，cloumn_key的值是二进制字节存储，具体value是字符串
        """
        if len(row_data) == 0:
            return None
        field_data_maps = cls.deserialize_row_key(row_key)
        for column_key, column_value in row_data.items():
            # 分别把key和value反序列化，先把key先反序列化
            field_name = column_key.decode('utf-8')
            index = field_name.find(':')
            # 没找到:时，直接把整个key当作field name
            field_name = field_name[index + 1:]
            # 把data中的value也反序列化
            column_value = column_value.decode('utf-8')
            field_value = cls.deserialize_field(field_name, column_value)
            field_data_maps[field_name] = field_value
        return cls(**field_data_maps)

    @classmethod
    def get_table(cls):
        """
        连接HBase数据库，获取对应数据表table
        """
        conn = HBaseClient.get_connection()
        return conn.table(cls.get_table_name())

    @classmethod
    def get(cls, **kwargs):
        row_key = cls.serialize_row_key(kwargs)
        table = cls.get_table()
        row_data = table.row(row_key)
        return cls.init_from_row(row_key, row_data)

    def save(self, batch=None):
        """
        用类似django model的方式对实例对应的数据，进行保存修改
        """

        row_data = self.serialize_row_data(self.__dict__)
        if not row_data:
            raise EmptyColumnError("columns should not be empty")
        if batch is not None:
            batch.put(self.row_key, row_data)
        else:
            table = self.get_table()
            table.put(self.row_key, row_data)

    @classmethod
    def create(cls, batch=None, **kwargs):
        """
        用类似django model的方式，以类方法创建一个实例，如XXXHBaseModel.create(a=x,b=y,c=z)
        """
        logger.info(f"Create cell in hbase table {cls.get_table_name()} with values {kwargs}")
        instance = cls(**kwargs)
        instance.save(batch=batch)
        logger.info(f"Hbase created cell in table {cls.get_table_name()} with data: {instance}")
        return instance

    @classmethod
    def batch_create(cls, batch_data):
        """
        批量创建
        """
        logger.info(f"Batch create cell in hbase table {cls.get_table_name()} with batch data {batch_data}")

        table = cls.get_table()
        batch = table.batch()
        results = []
        for data in batch_data:
            results.append(cls.create(batch=batch, **data))
        batch.send()
        return results

    @classmethod
    def get_table_name(cls):
        if not cls.Meta.table_name:
            raise NotImplementedError("Missing table name in HBaseModel Meta class")
        if settings.TESTING:
            return 'test_{}'.format(cls.Meta.table_name)
        return cls.Meta.table_name

    @classmethod
    def drop_table(cls):
        if not settings.TESTING:
            raise Exception('You cannot create table outside of unit tests')
        conn = HBaseClient.get_connection()
        conn.delete_table(cls.get_table_name(), True)

    @classmethod
    def create_table(cls):
        """
        仅用于测试的创建表
        """
        if not settings.TESTING:
            raise Exception('You cannot create table outside of unit tests')
        conn = HBaseClient.get_connection()
        # convert bytes to string
        tables = [table.decode('utf-8') for table in conn.tables()]
        if cls.get_table_name() in tables:
            return
        column_families = {
            field_type.column_family: dict()
            for field_name, field_type in cls.get_field_maps().items()
            if field_type.column_family is not None
        }
        conn.create_table(cls.get_table_name(), column_families)

    @classmethod
    def serialize_row_key_from_tuple(cls, row_key_tuple):
        """
        当我们以tuple而且不是dict形式传入row_key时，进行serialize，支持可以只serialize前缀部分
        """
        if row_key_tuple is None:
            return None
        data = {
            key: value
            for key, value in zip(cls.Meta.row_key, row_key_tuple)
        }
        return cls.serialize_row_key(data, is_prefix=True)

    @classmethod
    def filter(cls, start=None, stop=None, prefix=None, limit=None, reverse=False):
        """
        对表进行scan
        start, stop, prefix是针对于row_key，传入一个tuple，区间start，stop 左闭右开 [)，与python列表表示方式一致
        比如row_key有两部分（id， timestamp），可以传入start=（1, 15231xxx），
        不需要使用dict，因为我们在使用时并不关心row_key组成部分的名字，而只使用row_key组成部分的值
        limit 最大返回数量
        是否反向scan，比如start=10, stop=1, reverse=True则从10到1反向返回值
        """
        logger.info("filter table {}, start={}, stop={}, prefix={}, limit={}, reverse={}".format(
            cls.get_table_name(),
            start,
            stop,
            prefix,
            limit,
            reverse
        ))
        row_start = cls.serialize_row_key_from_tuple(start)
        row_stop = cls.serialize_row_key_from_tuple(stop)
        row_prefix = cls.serialize_row_key_from_tuple(prefix)

        # scan table
        table = cls.get_table()
        rows = table.scan(row_start, row_stop, row_prefix, limit=limit, reverse=reverse)

        results = []
        for row_key, row_data in rows:
            instance = cls.init_from_row(row_key, row_data)
            results.append(instance)
        logger.info(f"filter get results: {results}")
        return results

    @classmethod
    def delete(cls, **kwargs):
        row_key = cls.serialize_row_key(kwargs)
        table = cls.get_table()
        return table.delete(row_key)
