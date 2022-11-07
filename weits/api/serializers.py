from accounts.api.serializers import UserSerializerForWeit
from comments.api.serializers import CommentSerializer
from likes.api.serializers import LikeSerializer
from likes.serivces import LikeService
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from weits.constants import WEIT_PHOTOS_UPLOAD_LIMIT
from weits.models import Weit
from weits.services import WeitService
from utils.redis_helper import RedisHelper



class WeitSerializer(serializers.ModelSerializer):
    # need to get not only user id but also user other info
    user = UserSerializerForWeit(source='cached_user')
    has_liked = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    photo_urls = serializers.SerializerMethodField()

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
            'photo_urls',
        )

    def get_has_liked(self, obj):
        return LikeService.has_liked(self.context['request'].user, obj)

    def get_comments_count(self, obj):
        # name_set track the 'name' objects whose foreign are weit, 反查机制
        # return obj.comment_set.count()
        return RedisHelper.get_count(obj, 'comments_count')

    def get_likes_count(self, obj):
        # return obj.like_set.count()
        return RedisHelper.get_count(obj, 'likes_count')

    def get_photo_urls(self, obj):
        photo_urls = []
        for photo in obj.weitphoto_set.all().order_by('order'):
            photo_urls.append(photo.file.url)
        return photo_urls


class WeitSerializerForDetail(WeitSerializer):
    # use name_set to back trace foreign key, and remeber many=True
    comments = CommentSerializer(source='comment_set', many=True)
    likes = LikeSerializer(source='like_set', many=True)

    # override the Meta class in super class WeitSerializer
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
            'photo_urls',
        )

    # use serializer method to implement comment injection
    # comments = serializers.SerializerMethodField()
    # def get_comments(self, obj):
    #     return CommentSerializer(obj.comment_set.all(), many=True).data


class WeitSerializerForCreate(serializers.ModelSerializer):
    content = serializers.CharField(min_length=6, max_length=140)
    files = serializers.ListField(
        child=serializers.FileField(),
        allow_empty=True,
        required=False,
    )

    class Meta:
        model = Weit
        fields = ('content', 'files')

    def validate(self, data):
        if len(data.get('files', [])) > WEIT_PHOTOS_UPLOAD_LIMIT:
            raise ValidationError({
                'message': f'You can upload {WEIT_PHOTOS_UPLOAD_LIMIT} photos '
                            'at most'
            })
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        content = validated_data['content']
        weit = Weit.objects.create(user=user, content=content)
        if validated_data.get('files'):
            WeitService.create_photos_from_files(
                weit,
                validated_data['files'],
            )
        return weit
