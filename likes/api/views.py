from django.utils.decorators import method_decorator
from inbox.services import NotificationService
from likes.api.serializers import LikeSerializer, LikeSerializerForCreate, LikeSerializerForCancel
from likes.models import Like
from ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utils.decorators import required_params


class LikeViewSet(viewsets.GenericViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializerForCreate
    permission_classes = [IsAuthenticated]

    @required_params(method='POST', params=['content_type', 'object_id'])
    @method_decorator(ratelimit(key='user', rate='10/s', method='POST', block=True))
    def create(self, request, *args, **kwargs):
        serializer = LikeSerializerForCreate(
            data=request.data,
            context={'request': request},
        )

        if not serializer.is_valid():
            return Response({
                'message': "Please check your input",
                'success': False,
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        instance, created = serializer.get_or_create()
        if created:
            NotificationService.send_like_notification(instance)
        return Response(LikeSerializer(instance).data, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=False)
    @required_params(method='POST', params=['content_type', 'object_id'])
    @method_decorator(ratelimit(key='user', rate='10/s', method='POST', block=True))
    def cancel(self, request):
        serializer = LikeSerializerForCancel(
            data=request.data,
            context={'request': request},
        )

        if not serializer.is_valid():
            return Response({
                'message': "Please check your input",
                'success': False,
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        deleted = serializer.cancel()
        return Response({'success': True, 'deleted': deleted})
