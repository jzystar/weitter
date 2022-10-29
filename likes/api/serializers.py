from accounts.api.serializers import UserSerializerForLike
from comments.models import Comment
from django.contrib.contenttypes.models import ContentType
from likes.models import Like
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from weits.models import Weit


class LikeSerializer(serializers.ModelSerializer):
    # use cache from UserService functions here, but we have to implement get_user func for each like serializer which used UserSerializer
    # so we can use 'source' instead
    # user = serializers.SerializerMethodField()

    # use 'source', so we have to implement source property 'cached_user' in like model
    user = UserSerializerForLike(source='cached_user')


    class Meta:
        model = Like
        fields = ('user', 'created_at')

    # def get_user(self, obj):
    #     from accounts.services import UserService
    #     user = UserService.get_user_through_cache(obj.user_id)
    #     return UserSerializerForLike(instance=user)


class LikeSerializerForCreateAndCancel(serializers.ModelSerializer):
    content_type = serializers.ChoiceField(choices=['comment', 'weit'])
    object_id = serializers.IntegerField()

    class Meta:
        model = Like
        fields = ('content_type', 'object_id')

    def _get_model_class(self, data):
        if data.get('content_type') == 'comment':
            return Comment
        if data.get('content_type') == 'weit':
            return Weit
        return None

    def validate(self, data):
        model_class = self._get_model_class(data)
        if model_class is None:
            raise ValidationError({'content_type': 'Content type does not exist'})
        liked_object = model_class.objects.filter(id=data['object_id']).first()
        if liked_object is None:
            raise ValidationError({'object_id': 'Object does not exist'})
        return data


class LikeSerializerForCreate(LikeSerializerForCreateAndCancel):

    def get_or_create(self):
        model_class = self._get_model_class(self.validated_data)
        return Like.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(model_class),
            object_id=self.validated_data['object_id'],
            user=self.context['request'].user,
        )

class LikeSerializerForCancel(LikeSerializerForCreateAndCancel):

    def cancel(self):
        # self.validated_data is set when is_valid is called
        model_class = self._get_model_class(self.validated_data)
        deleted, _ = Like.objects.filter(
            content_type=ContentType.objects.get_for_model(model_class),
            object_id=self.validated_data['object_id'],
            user=self.context['request'].user,
        ).delete()
        return deleted
