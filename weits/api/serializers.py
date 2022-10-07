from accounts.api.serializers import UserSerializerForWeit
from comments.api.serializers import CommentSerializer
from likes.api.serializers import LikeSerializer
from likes.serivces import LikeService
from rest_framework import serializers
from weits.models import Weit


class WeitSerializer(serializers.ModelSerializer):
    # need to get not only user id but also user other info
    user = UserSerializerForWeit()
    has_liked = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Weit
        fields = (
            'id',
            'user',
            'created_at',
            'content',
            'comments_count',
            'likes_count',
            'has_liked',
        )

    def get_has_liked(self, obj):
        return LikeService.has_liked(self.context['request'].user, obj)

    def get_comments_count(self, obj):
        # name_set track the 'name' objects whose foreign are weit, 反查机制
        return obj.comment_set.count()

    def get_likes_count(self, obj):
        return obj.like_set.count()


class WeitSerializerForDetail(WeitSerializer):
    # user name_set to back trace foreign key, and remeber many=True
    comments = CommentSerializer(source='comment_set', many=True)
    likes = LikeSerializer(source='like_set', many=True)

    class Meta:
        model = Weit
        fields = ('id', 'user', 'created_at', 'content', 'comments')
        fields = (
            'id',
            'user',
            'created_at',
            'content',
            'comments',
            'likes',
            'comments_count',
            'likes_count',
            'has_liked',
        )

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
