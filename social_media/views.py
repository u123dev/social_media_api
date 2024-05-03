from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from rest_framework import generics, viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from user.permissions import IsOwnerOrReadOnly
from social_media.serializers import (
    UserProfileListSerializer,
    UserProfileDetailSerializer,
    UserProfileSerializer,
    UserProfilePictureSerializer,
    UserFollowSerializer,
)


class UserProfileViewSet(
    #  mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    #  mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = get_user_model().objects.all().annotate(
        followers_count=(Count("followers", distinct=True)),
        followed_by_count=(Count("followed_by", distinct=True)),
    )
    permission_classes = [IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return UserProfileListSerializer
        if self.action == "retrieve":
            return UserProfileDetailSerializer
        if self.action == "upload":
            return UserProfilePictureSerializer
        if self.action in ("follow", "unfollow"):
            return UserFollowSerializer
        return UserProfileSerializer

    def get_queryset(self):
        queryset = self.queryset.prefetch_related("followers")
        # filtering by email, first_name, last_name
        name = self.request.query_params.get("name")
        if name:
            queryset = queryset.filter(
                Q(email__icontains=name)
                | Q(first_name__icontains=name)
                | Q(last_name__icontains=name)
            )
        return queryset

    @action(
        methods=["POST", "GET"],
        detail=True,
        url_path="picture",
        permission_classes=[IsOwnerOrReadOnly],
    )
    def set_picture(self, request, pk=None):
        """Endpoint for uploading picture of user profile"""
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["POST"],
            permission_classes=[IsAuthenticated])
    def follow(self, request, pk=None):
        user_to_follow = self.get_object()
        user_to_follow.followers.add(self.request.user)
        return Response(
            {"detail": ("Add follower: " + self.request.user.email
                        + " to: " + user_to_follow.email)},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["POST"],
            permission_classes=[IsAuthenticated])
    def unfollow(self, request, pk=None):
        user_to_unfollow = self.get_object()
        user_to_unfollow.followers.remove(self.request.user)
        return Response(
            {"detail": ("Delete follower: " + self.request.user.email
                        + " from: " + user_to_unfollow.email)},
            status=status.HTTP_200_OK
        )

    @action(methods=["GET"], detail=True, url_path="followers")
    def get_followers(self, request, pk=None):
        user = self.get_object()
        serializer = UserFollowSerializer(
            user.followers.all(), many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=["GET"], detail=True, url_path="followed-by")
    def get_followed_by(self, request, pk=None):
        user = self.get_object()
        followed_by = user.followed_by.all()
        serializer = UserFollowSerializer(followed_by, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
