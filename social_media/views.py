import base64
from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from rest_framework import generics, viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from social_media.models import Post, Comment
from social_media.permissions import IsOwnerOrReadOnly, IsOwnerUserOrReadOnly
from social_media.tasks import publish_post
from social_media.serializers import (
    UserProfileListSerializer,
    UserProfileDetailSerializer,
    UserProfileSerializer,
    UserProfilePictureSerializer,
    UserFollowSerializer,
    PostSerializer,
    PostDetailSerializer,
    PostListSerializer,
    PostUpdateSerializer,
    PostImageSerializer,
    CommentSerializer,
    PostLikeSerializer,
)


class UserProfileViewSet(
    # mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    # mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = get_user_model().objects.all().annotate(
        followers_count=(Count("followers", distinct=True)),
        followed_by_count=(Count("followed_by", distinct=True)),
    )
    permission_classes = [IsOwnerUserOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return UserProfileListSerializer
        if self.action == "retrieve":
            return UserProfileDetailSerializer
        if self.action == "set_picture":
            return UserProfilePictureSerializer
        if self.action in ("follow", "unfollow"):
            return UserFollowSerializer
        return UserProfileSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "retrieve":
            queryset = queryset.prefetch_related("followers")
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
        permission_classes=[IsOwnerUserOrReadOnly],
    )
    def set_picture(self, request, pk=None):
        """Endpoint for uploading user profile picture"""
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["POST"],
            permission_classes=[IsAuthenticated])
    def follow(self, request, pk=None):
        """Add current user to followers"""
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
        """Delete current user from followers"""
        user_to_unfollow = self.get_object()
        user_to_unfollow.followers.remove(self.request.user)
        return Response(
            {"detail": ("Delete follower: " + self.request.user.email
                        + " from: " + user_to_unfollow.email)},
            status=status.HTTP_200_OK
        )

    @action(methods=["GET"], detail=True, url_path="followers",
            permission_classes=[IsAuthenticated])
    def get_followers(self, request, pk=None):
        """List all followers"""
        user = self.get_object()
        serializer = UserFollowSerializer(
            user.followers.all(), many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=["GET"], detail=True, url_path="followed-by",
            permission_classes=[IsAuthenticated])
    def get_followed_by(self, request, pk=None):
        """List all users that followed by current user """
        user = self.get_object()
        followed_by = user.followed_by.all()
        serializer = UserFollowSerializer(followed_by, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PostPagination(PageNumberPagination):
    page_size = 3
    max_page_size = 100


class PostViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = Post.objects.annotate(
        likes_count=Count("likes", distinct=True),
        comments_count=Count("comments", distinct=True),
    ).select_related("user")
    serializer_class = PostSerializer
    pagination_class = PostPagination
    permission_classes = [
        IsAuthenticated,
    ]

    def get_permissions(self):
        """ Returns the list of permissions that this view requires."""
        if self.action in ("update", "partial_update"):
            permission_classes = [IsOwnerOrReadOnly]
        else:
            permission_classes = self.permission_classes
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer
        if self.action == "update":
            return PostUpdateSerializer
        if self.action == "retrieve":
            return PostDetailSerializer
        if self.action == "image":
            return PostImageSerializer
        if self.action == "comment":
            return CommentSerializer
        if self.action in ("like", "unlike"):
            return PostLikeSerializer

        return PostSerializer

    def get_queryset(self):
        queryset = self.queryset

        tag = self.request.query_params.get("tag")
        if tag:
            queryset = queryset.filter(content__icontains=tag)

        if self.action == "list":
            queryset = queryset.filter(
                Q(user=self.request.user)
                | Q(user__in=self.request.user.followed_by.values("id"))
            )

        return queryset

    def create(self, request, *args, **kwargs):
        user = request.user

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        post_at = request.data.get("post_at")

        if post_at:
            image = self.request.FILES.get("image")
            if image:
                image = image.read()
                byte = base64.b64encode(image)
                image_data = {
                    "image": byte.decode("utf-8"),
                    "name": self.request.FILES.get("image").name
                }
            else:
                image_data = None

            post_at = (datetime.strptime(post_at, "%Y-%m-%dT%H:%M")
                       .astimezone(timezone.utc))
            publish_post.apply_async(
                args=[request.data.get("content"),
                      image_data,
                      request.user.id],
                eta=post_at
            )
            return Response(f"Post will be published at {post_at} UTC",
                            status=status.HTTP_200_OK)

        serializer.save(user=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        methods=["POST", "GET"],
        detail=True,
        url_path="image",
        permission_classes=[IsOwnerOrReadOnly],
    )
    def image(self, request, pk=None):
        """Endpoint for uploading post image"""
        post = self.get_object()
        serializer = self.get_serializer(post, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=["POST"], detail=True)
    def comment(self, request, pk=None):
        """Endpoint for comment of post"""
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=False)
        serializer.save(
            post_id=pk,
            user=self.request.user,
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["POST"],
            permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        """Endpoint for like of post"""
        post_to_like = self.get_object()
        post_to_like.likes.add(self.request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["POST"],
            permission_classes=[IsAuthenticated])
    def unlike(self, request, pk=None):
        """Endpoint for inlike of post"""
        post_to_like = self.get_object()
        post_to_like.likes.remove(self.request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["GET"], url_path="liked_posts",
            permission_classes=[IsAuthenticated])
    def liked_posts(self, request, pk=None):
        """Endpoint for list of all liked post by current user"""
        posts = Post.objects.filter(likes=self.request.user)
        serializer = PostListSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    permission_classes = [
        IsOwnerOrReadOnly,
    ]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CommentSerializer
        return CommentSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(user_id=self.request.user.id)
        return queryset
