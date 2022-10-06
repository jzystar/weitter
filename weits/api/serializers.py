from accounts.api.serializers import UserSerializerForWeit
from comments.api.serializers import CommentSerializer
from rest_framework import serializers
from weits.models import Weit


class WeitSerializer(serializers.ModelSerializer):
    # need to get not only user id but also user other info
    user = UserSerializerForWeit()

    class Meta:
        model = Weit
        fields = ('id', 'user', 'created_at', 'content')

class WeitSerializerWithComments(WeitSerializer):
    # user name_set to back trace foreign key, and remeber many=True
    comments = CommentSerializer(source='comment_set', many=True)

    class Meta:
        model = Weit
        fields = ('id', 'user', 'created_at', 'content', 'comments')

    # use serializer method to implement comment injection
    # comments = serializers.SerializerMethodField()
    # def get_comments(self, obj):
    #     return CommentSerializer(obj.comment_set.all(), many=True).data


class WeitSerializerForCreate(serializers.ModelSerializer):
    content = serializers.CharField(min_length=6, max_length=140)

    class Meta:
        model = Weit
        fields = ('content',)

    def create(self, validated_data):
        user = self.context['request'].user
        weit = Weit.objects.create(user=user, content=validated_data['content'])
        return weit
