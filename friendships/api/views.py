from django.contrib.auth.models import User
from friendships.api.paginations import FriendshipPagination
from friendships.api.serializers import (
    FollowerSerializer,
    FollowingSerializer,
    FriendshipSerializerForCreate,
)
from friendships.models import Friendship
from friendships.services import FriendshipServices
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response


class FriendshipViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = FriendshipSerializerForCreate
    # 定义翻页功能pagination
    pagination_class = FriendshipPagination

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    def followers(self, request, pk):
        # GET /api/friendships/1/followers/
        friendships = Friendship.objects.filter(to_user_id=pk).order_by('-created_at')
        page = self.paginate_queryset(friendships)
        serializer = FollowerSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    def followings(self, request, pk):
        friendships = Friendship.objects.filter(from_user_id=pk).order_by('-created_at')
        page = self.paginate_queryset(friendships)
        serializer = FollowingSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    def follow(self, request, pk):
        # get_object 会去拿pk的对应object，拿不到返回404，这样可以省去后面对于pk值不存在的valid的判断
        self.get_object()
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
            'to_user_id': pk
        })
        if not serializer.is_valid():
            return Response({
                "success": False,
                'message': "Please check input",
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        instance = serializer.save()
        # 记得更新缓存，一般是删掉当前对应的缓存，如果有的话
        FriendshipServices.invalidate_following_cache(request.user.id)
        return Response(
            FollowingSerializer(instance, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    def unfollow(self, request, pk):
        # raise 404 if no user_id = pk
        unfollow_user = self.get_object()
        if request.user.id == int(pk):
            return Response({
                'success': False,
                'message': 'You can not unfollow yourself',
            }, status=status.HTTP_400_BAD_REQUEST)
        # deleted 是删了多少数据，第二个_的返回值是具体每种类型删了多少（考虑到cascade的级联删除的可能）
        deleted, _ = Friendship.objects.filter(
            from_user=request.user,
            to_user=unfollow_user,
        ).delete()
        FriendshipServices.invalidate_following_cache(request.user.id)
        return Response({'success': True, 'deleted': deleted})

    def list(self, request):
        return Response({'message': 'this is friendship'})
