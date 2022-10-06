from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from accounts.api.serializers import UserSerializerForComment
from comments.models import Comment
from weits.models import Weit


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializerForComment()

    class Meta:
        model = Comment
        fields = ('id', 'weit_id', 'user', 'content', 'created_at', 'updated_at')


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