from inbox.api.serializers import (
    NotificationSerializer,
    NotificationSerializerForUpdate,
)
from notifications.models import Notification
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utils.decorators import required_params


class NotificationViewSet(
    viewsets.GenericViewSet,
    viewsets.mixins.ListModelMixin,
):
    # serializer_class is used for list method in ListModelMixin
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated, )
    # used for 'list' method in viewsets.mixins.ListModelMixin
    filterset_fields = ('unread', )

    def get_queryset(self):
        # Notification use User as ForeignKey, and user related name is 'notifications'
        # so we can use notifications instead of notification_set to back retrieve notifications
        return self.request.user.notifications.all()
        # return Notification.objects.filter(recipient=self.request.user)

    @action(methods=['GET'], detail=False, url_path='unread-count')
    def unread_count(self, request, *args, **kwargs):
        count = self.get_queryset().filter(unread=True).count()
        return Response({'unread_count': count}, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False, url_path='mark-all-as-read')
    def mark_all_as_read(self, request, *arg, **kwargs):
        marked_count = self.get_queryset().filter(unread=True).update(unread=False)
        return Response({'marked_count': marked_count}, status=status.HTTP_200_OK)

    @required_params(method='POST', params=['unread'])
    def update(self, request, *args, **kwargs):
        serializer = NotificationSerializerForUpdate(
            instance=self.get_object(),
            data=request.data,
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': "Please check your input",
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        notification = serializer.save()
        return Response(
            NotificationSerializer(notification).data,
            status=status.HTTP_200_OK,
        )


