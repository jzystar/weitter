from accounts.api.serializers import UserSerializerForComment
from comments.models import Comment
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from likes.serivces import LikeService
from weits.models import Weit


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializerForComment(source='cached_user')
    has_liked = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            'id',
            'weit_id',
            'user',
            'content',
            'created_at',
            'updated_at',
            'has_liked',
            'likes_count',
        )

    def get_has_liked(self, obj):
        return LikeService.has_liked(self.context['request'].user, obj)

    def get_likes_count(self, obj):
        # return obj.like_set.count()
        return obj.like_count


class CommentSerializerForCreate(serializers.ModelSerializer):
    user_id = serializers.IntegerField()
    weit_id = serializers.IntegerField()

    class Meta:
        model = Comment
        fields = ('user_id', 'weit_id', 'content')

    def validate(self, data):
        weit_id = data['weit_id']
        if not Weit.objects.filter(id=weit_id).exists():
            raise ValidationError({'message': 'weit does not exist'})
        return data


class CommentSerializerForUpdate(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('content',)

    def update(self, instance, validated_data):
        instance.content = validated_data['content']
        instance.save()
        return instance
