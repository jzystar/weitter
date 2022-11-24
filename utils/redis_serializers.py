from django.core import serializers
from django_hbase.models import HBaseModel
from utils.json_encoder import JSONEncoder

import json


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


class HBaseModelSerializer:

    @classmethod
    def get_model_class(cls, model_class_name):
        for subclass in HBaseModel.__subclasses__():
            if subclass.__name__ == model_class_name:
                return subclass
        raise Exception('HBaseModel {} not found'.format(model_class_name))

    @classmethod
    def serialize(cls, instance: HBaseModel):
        json_data = {'model_class_name': instance.__class__.__name__}
        for key in instance.get_field_maps():
            value = getattr(instance, key)
            json_data[key] = value
        return json.dumps(json_data)

    @classmethod
    def deserialize(cls, serialized_data):
        json_data = json.loads(serialized_data)
        model_class = cls.get_model_class(json_data['model_class_name'])
        del json_data['model_class_name']
        return model_class(**json_data)
