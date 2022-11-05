from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.services import NewsFeedServices
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from utils.paginations import EndlessPagination


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination

    # def get_queryset(self):
    #     return NewsFeed.objects.filter(user=self.request.user)

    def list(self, request):
        queryset = NewsFeedServices.get_cached_newsfeeds(request.user.id)
        page = self.paginate_queryset(queryset)

        serializer = NewsFeedSerializer(
            page,
            context={'request': request},
            many=True,
        )
        return self.get_paginated_response(serializer.data)

