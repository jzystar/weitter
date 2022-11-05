from django.core import serializers
from utils.json_encoder import JSONEncoder


class DjangoModelSerializer:

    @classmethod
    def serialize(cls, instance):
        # Django 的 serializers 默认需要QuerySet或list 类型的数据来做序列化
        # 因此需要给instance 加一个[]变成list
        return serializers.serialize('json', [instance], cls=JSONEncoder)

    @classmethod
    def deserialize(cls, serialize_data):
        # need to get .object for model object, because deserialize() return a DeserializedObject
        return list(serializers.deserialize('json', serialize_data))[0].object
