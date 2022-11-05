from newsfeeds.services import NewsFeedServices
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from utils.decorators import required_params
from utils.paginations import EndlessPagination
from weits.api.serializers import WeitSerializer, WeitSerializerForCreate, WeitSerializerForDetail
from weits.models import Weit
from weits.services import WeitService


class WeitViewSet(viewsets.GenericViewSet):
    queryset = Weit.objects.all()
    serializer_class = WeitSerializerForCreate
    pagination_class = EndlessPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @required_params(params=['user_id'])
    def list(self, request):
        # weits = Weit.objects.filter(
        #     user_id=request.query_params['user_id']
        # ).prefetch_related('user').order_by('-created_at')
        # use cache for listing weits
        user_id = request.query_params['user_id']
        cached_weits = WeitService.get_cached_weits(user_id)
        page = self.paginator.paginate_cached_list(cached_weits, request)
        # page is None means 目前数据不在cache里（超过了cache的size), 直接去数据库取
        if page is None:
            queryset = Weit.objects.filter(user_id=user_id).order_by('-created_at')
            page = self.paginate_queryset(queryset)

        serializer = WeitSerializer(
            page,
            context={'request': request},
            many=True,
        )

        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        weit = self.get_object()
        serializer = WeitSerializerForDetail(
            weit,
            context={'request': request},
        )
        return Response(serializer.data)

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
        return Response(WeitSerializer(
            weit,
            context={'request': request}).data,
            status=201,
        )
