from dateutil import parser
from django.conf import settings
from django_hbase.models import HBaseModel
from rest_framework.pagination import BasePagination
from rest_framework.response import Response
from utils.time_constants import MAX_TIMESTAMP


class EndlessPagination(BasePagination):
    page_size = 20

    def __init__(self):
        super(EndlessPagination, self).__init__()
        self.has_next_page = False

    def to_html(self):
        pass

    def paginate_ordered_list(self, reversed_ordered_list, request):
        if 'created_at__gt' in request.query_params:
            # 兼容iso和int格式的时间戳, TODO: 最好还是统一时间戳格式
            try:
                created_at__gt = parser.isoparse(request.query_params['created_at__gt'])
            except ValueError:
                created_at__gt = int(request.query_params['created_at__gt'])

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
            try:
                created_at__lt = parser.isoparse(request.query_params['created_at__lt'])
            except ValueError:
                created_at__lt = int(request.query_params['created_at__lt'])
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

    def paginate_hbase(self, hb_model: HBaseModel, row_key_prefix, request):
        if 'created_at__gt' in request.query_params:
            # created_at__gt 用于下拉刷新的时候加载最新的内容进来
            # 为了简便起见，下拉刷新不做翻页机制，直接加载所有更新的数据
            # 因为如果数据很久没有更新的话，不会采用下拉刷新的方式进行更新，而是重新加载最新的数据
            created_at__gt = request.query_params['created_at__gt']
            start = (*row_key_prefix, created_at__gt)
            stop = (*row_key_prefix, MAX_TIMESTAMP)
            objects = hb_model.filter(start=start, stop=stop)
            if len(objects) and objects[0].created_at == int(created_at__gt):
                objects = objects[:0:-1]
            else:
                objects = objects[::-1]
            self.has_next_page = False
            return objects

        if 'created_at__lt' in request.query_params:
            # created_at__lt 用于向上滚屏（往下翻页）的时候加载下一页的数据
            # 寻找 timestamp < created_at__lt 的 objects 里
            # 按照 timestamp 倒序的前 page_size + 1 个 objects
            # 比如目前的 timestamp 列表是 [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            # 如果 created_at__lt=5, page_size = 2，则应该返回 [4, 3, 2]，
            # 多返回一个 object 的原因是为了判断是否还有下一页从而减少一次空加载。
            # 由于 hbase 只支持 <= 的查询而不支持 <,
            # 因此我们还需要再多取一个 item 保证 < 的 item 有 page_size + 1 个
            # 故 limit=page_size + 2
            created_at__lt = request.query_params['created_at__lt']
            start = (*row_key_prefix, created_at__lt)
            stop = (*row_key_prefix, None)

            objects = hb_model.filter(start=start, stop=stop, limit=self.page_size + 2, reverse=True)
            if len(objects) and objects[0].created_at == int(created_at__lt):
                objects = objects[1:]
            if len(objects) > self.page_size:
                self.has_next_page = True
                objects = objects[ : -1]
            else:
                self.has_next_page = False
            return objects

        # 没有任何参数，默认加载最新一页
        prefix = (*row_key_prefix, None)
        objects = hb_model.filter(prefix=prefix, limit=self.page_size + 1, reverse=True)
        if len(objects) > self.page_size:
            self.has_next_page = True
            objects = objects[:-1]
        else:
            self.has_next_page = False
        return objects
