from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from weits.models import Weit
from weits.api.serializers import WeitSerializer, WeitSerializerForCreate
from newsfeeds.services import NewsFeedServices


class WeitViewSet(viewsets.GenericViewSet):
    serializer_class = WeitSerializerForCreate

    def get_permissions(self):
        if self.action == 'list':
            return [AllowAny()]
        return [IsAuthenticated()]

    def list(self, request):
        if 'user_id' not in request.query_params:
            return Response("missing user id", status=400)

        weits = Weit.objects.filter(
            user_id=request.query_params['user_id']
        ).order_by('-created_at')
        serializer = WeitSerializer(weits, many=True)
        return Response({"weits": serializer.data})

    def create(self, request):
        serializer = WeitSerializerForCreate(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Please check input.',
                'errors': serializer.errors,
            }, status=400)
        weit = serializer.save()
        NewsFeedServices.fanout_to_followers(weit)
        return Response(WeitSerializer(weit).data, status=201)
