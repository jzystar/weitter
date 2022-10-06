from newsfeeds.services import NewsFeedServices
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from utils.decorators import required_params
from weits.api.serializers import WeitSerializer, WeitSerializerForCreate, WeitSerializerWithComments
from weits.models import Weit


class WeitViewSet(viewsets.GenericViewSet):
    queryset = Weit.objects.all()
    serializer_class = WeitSerializerForCreate

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @required_params(params=['user_id'])
    def list(self, request):
        weits = Weit.objects.filter(
            user_id=request.query_params['user_id']
        ).prefetch_related('user').order_by('-created_at')
        serializer = WeitSerializer(weits, many=True)
        return Response({"weits": serializer.data})

    def retrieve(self, request, *args, **kwargs):
        weit = self.get_object()
        return Response(WeitSerializerWithComments(weit).data)

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
