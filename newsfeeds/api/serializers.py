from rest_framework import serializers
from weits.api.serializers import WeitSerializer


class NewsFeedSerializer(serializers.Serializer):
    weit = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass
    
    def get_weit(self, obj):
        return WeitSerializer(obj.cached_weit, context=self.context).data

    def get_created_at(self, obj):
        return obj.created_at
