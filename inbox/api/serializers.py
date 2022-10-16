from notifications.models import Notification
from rest_framework import serializers


class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        '''
        1. user1 followed you
            actor_content_type = User
            actor_object_id = user1.id
            (actor = user1)
            verb = 'follow'
            
        2. user1 likes your weit1
            actor_content_type = User
            actor_object_id = user1.id
            verb = 'like your weit {target}'
            target_content_type = Weit
            target_object_id = weit.id
            (target = weit1)
        '''
        fields = (
            'id',
            'actor_content_type',
            'actor_object_id',
            'verb',
            'action_object_content_type',
            'action_object_object_id',
            'target_content_type',
            'target_object_id',
            'unread',
            'timestamp',
        )


class NotificationSerializerForUpdate(serializers.ModelSerializer):
    # BooleanField can recognize true, True, "True", "true", 0, 1
    unread = serializers.BooleanField()

    class Meta:
        model = Notification
        fields = ('unread', )

    def update(self, instance, validated_data):
        instance.unread = validated_data['unread']
        instance.save()
        return instance
