from rest_framework.pagination import BasePagination
from rest_framework.response import Response
from dateutil import parser
from django.conf import settings


class EndlessPagination(BasePagination):
    page_size = 20

    def __init__(self):
        super(EndlessPagination, self).__init__()
        self.has_next_page = False

    def to_html(self):
        pass

    def paginate_ordered_list(self, reversed_ordered_list, request):
        # now we assume that all data are cached in redis, TODO: cache size limitation
        if 'created_at__gt' in request.query_params:
            created_at__gt = parser.isoparse(request.query_params['created_at__gt'])
            objects = []
            for obj in reversed_ordered_list:
                if obj.created_at > created_at__gt:
                    objects.append(obj)
                else:
                    break
            self.has_next_page = False
            return objects
        index = 0
        if 'created_at__lt' in request.query_params:
            created_at__lt = parser.isoparse(request.query_params['created_at__lt'])
            for index, obj in enumerate(reversed_ordered_list):
                if obj.created_at < created_at__lt:
                    break
            else:
                # 没找到满足条件的objects，return None
                reversed_ordered_list = []
        self.has_next_page = len(reversed_ordered_list) > index + self.page_size
        return reversed_ordered_list[index: index + self.page_size]

    def paginate_queryset(self, queryset, request, view=None):
        # if queryset is a list, which means paginate redis cached queryset list
        # use paginate_ordered_list method
        # deprecated after cache limit is set
        # if type(queryset) == list:
        #     return self.paginate_ordered_list(queryset, request)

        # 下拉向上翻页，直接返回比当前第一个更新的weits，
        # 若长时间没有上翻过，则不应用上翻更新了，而是应该重新加载最新的weits
        if 'created_at__gt' in request.query_params:
            created_at__gt = request.query_params['created_at__gt']
            queryset = queryset.filter(created_at__gt=created_at__gt)
            self.has_next_page = False
            return queryset.order_by('-created_at')

        if 'created_at__lt' in request.query_params:
            created_at__lt = request.query_params['created_at__lt']
            queryset = queryset.filter(created_at__lt=created_at__lt)

        # 不带参数的翻页
        # 多取一个，用来查看是否有下一页
        queryset = queryset.order_by('-created_at')[:self.page_size + 1]
        self.has_next_page = len(queryset) > self.page_size
        return queryset[:self.page_size]

    def paginate_cached_list(self, cached_list, request):
        paginated_list = self.paginate_ordered_list(cached_list, request)
        # 若是上翻页，则是希望返回最新的数据，可以直接返回
        if 'created_at__gt' in request.query_params:
            return paginated_list
        # 下翻页，且cache里还有下一页的话，也是直接返回
        if self.has_next_page:
            return paginated_list
        # 没有下一页的话，若cache list未达到最大值，也可以直接返回，此时说明数据库里也没有了
        if len(cached_list) < settings.REDIS_LIST_LENGTH_LIMIT:
            return paginated_list

        # cache_list 满了，且没有下一页了，则直接返回None，后面需要去数据库里面取了
        return None

    def get_paginated_response(self, data):
        return Response({
            'has_next_page': self.has_next_page,
            'results': data,
        })