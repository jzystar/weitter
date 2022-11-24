from django.utils.decorators import method_decorator
from gatekeeper.models import GateKeeper
from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.models import NewsFeed, HBaseNewsFeed
from newsfeeds.services import NewsFeedServices
from ratelimit.decorators import ratelimit
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from utils.paginations import EndlessPagination


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination

    def get_queryset(self):
        return NewsFeed.objects.filter(user=self.request.user)

    @method_decorator(ratelimit(key='user', rate='3/s', method='GET', block=True))
    def list(self, request):
        cached_newsfeeds = NewsFeedServices.get_cached_newsfeeds(request.user.id)
        paginator = self.paginator
        page = paginator.paginate_cached_list(cached_newsfeeds, request)
        # page is None means 目前数据不在cache里（超过了cache的size), 直接去数据库取
        if page is None:
            if GateKeeper.is_switch_on('switch_newsfeed_to_hbase'):
                page = paginator.paginate_hbase(
                    HBaseNewsFeed,
                    (request.user.id, ),
                    request
                )
            else:
                queryset = self.get_queryset()
                page = self.paginate_queryset(queryset)

        serializer = NewsFeedSerializer(
            page,
            context={'request': request},
            many=True,
        )
        return self.get_paginated_response(serializer.data)

