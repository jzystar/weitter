from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from friendships.api.serializers import (
    FollowerSerializer,
    FollowingSerializer,
    FriendshipSerializerForCreate,
)
from friendships.models import Friendship, HBaseFollowing, HBaseFollower
from friendships.services import FriendshipServices
from gatekeeper.models import GateKeeper
from ratelimit.decorators import ratelimit
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from utils.paginations import EndlessPagination



class FriendshipViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = FriendshipSerializerForCreate
    # 定义翻页功能pagination
    pagination_class = EndlessPagination

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    @method_decorator(ratelimit(key='user_or_ip', rate='3/s', method='GET', block=True))
    def followers(self, request, pk):
        # GET /api/friendships/1/followers/
        pk = int(pk)
        paginator = self.paginator
        if GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            page = paginator.paginate_hbase(HBaseFollower, (pk, ), request)
        else:
            friendships = Friendship.objects.filter(to_user_id=pk).order_by('-created_at')
            page = paginator.paginate_queryset(friendships, request)

        serializer = FollowerSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    @method_decorator(ratelimit(key='user_or_ip', rate='3/s', method='GET', block=True))
    def followings(self, request, pk):
        pk = int(pk)
        paginator = self.paginator
        if GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            page = paginator.paginate_hbase(HBaseFollowing, (pk, ), request)
        else:
            friendships = Friendship.objects.filter(from_user_id=pk).order_by('-created_at')
            page = paginator.paginate_queryset(friendships, request)

        serializer = FollowingSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    @method_decorator(ratelimit(key='user', rate='10/s', method='POST', block=True))
    def follow(self, request, pk):
        # get_object 会去拿pk的对应object，拿不到返回404，这样可以省去后面对于pk值不存在的valid的判断
        to_follow_user = self.get_object()

        if FriendshipServices.has_followed(request.user.id, to_follow_user.id):
            return Response({
                'success': False,
                'message': "Please check input",
                'errors': [{
                    'pk': f'You have followed user with id={pk}'
                }],
            }, status=status.HTTP_400_BAD_REQUEST)
        '''
        if Friendship.objects.filter(
            from_user=request.user,
            to_user_id=pk
        ).exists():
            return Response({
                'success': True,
                'duplicated': True,
            }, status=status.HTTP_201_CREATED)
        '''
        serializer = FriendshipSerializerForCreate(data={
            'from_user_id': request.user.id,
            'to_user_id': to_follow_user.id,
        })
        if not serializer.is_valid():
            return Response({
                "success": False,
                'message': "Please check input",
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        instance = serializer.save()
        # 记得更新缓存，一般是删掉当前对应的缓存，如果有的话
        # FriendshipServices.invalidate_following_cache(request.user.id)
        return Response(
            FollowingSerializer(instance, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    @method_decorator(ratelimit(key='user', rate='10/s', method='POST', block=True))
    def unfollow(self, request, pk):
        # raise 404 if no user_id = pk
        unfollow_user = self.get_object()
        if request.user.id == unfollow_user.id:
            return Response({
                'success': False,
                'message': 'You can not unfollow yourself',
            }, status=status.HTTP_400_BAD_REQUEST)
        # deleted 是删了多少数据，第二个_的返回值是具体每种类型删了多少（考虑到cascade的级联删除的可能）
        # deleted, _ = Friendship.objects.filter(
        #     from_user=request.user,
        #     to_user=unfollow_user,
        # ).delete()
        # FriendshipServices.invalidate_following_cache(request.user.id)
        deleted = FriendshipServices.unfollow(request.user.id, unfollow_user.id)
        return Response({'success': True, 'deleted': deleted})

    def list(self, request):
        return Response({'message': 'this is friendship'})
