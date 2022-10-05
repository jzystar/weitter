from rest_framework import serializers
from newsfeeds.models import NewsFeed
from weits.api.serializers import WeitSerializer


class NewsFeedSerializer(serializers.ModelSerializer):
    weit = WeitSerializer()
    
    class Meta:
        model = NewsFeed
        fields = ('id', 'weit', 'created_at')

