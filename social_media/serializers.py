from django.contrib.auth import get_user_model
from rest_framework import serializers

from social_media.models import Post, Comment


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "email",
            "full_name",
            "first_name",
            "last_name",
            "bio",
            "location",
            "followers",
            "profile_picture",
        )
        read_only_fields = ("email", "full_name", "profile_picture", )


class UserProfilePictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "email", "full_name", "profile_picture")
        read_only_fields = ("email", "full_name", )


class UserProfileListSerializer(serializers.ModelSerializer):
    followers_count = serializers.IntegerField(read_only=True)
    followed_by_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "email",
            "full_name",
            "location",
            "followers_count",
            "followed_by_count",
            "profile_picture",
        )


class UserProfileDetailSerializer(serializers.ModelSerializer):
    followers_count = serializers.IntegerField(read_only=True)
    followers = serializers.SlugRelatedField(slug_field="email",
                                             read_only=True, many=True)
    followed_by_count = serializers.IntegerField(read_only=True)
    followed_by = serializers.SlugRelatedField(slug_field="email",
                                               read_only=True, many=True)

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "email",
            "full_name",
            "bio",
            "location",
            "followers_count",
            "followers",
            "followed_by_count",
            "followed_by",
            "profile_picture",
        )


class UserFollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "email", "full_name", "profile_picture", )
        read_only_fields = ("email", "full_name", "profile_picture", )


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field="email", read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "user", "post", "message", "created_at", )
        read_only_fields = ("post", )
        ordering = ("-created_at", )


class PostSerializer(serializers.ModelSerializer):
    post_at = serializers.DateTimeField(
        write_only=False, required=False
    )

    class Meta:
        model = Post
        fields = ("id", "content", "created_at", "post_at", "image", "likes")


class PostUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("id", "content", "created_at", )


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("id", "user", "image", )
        read_only_fields = ("user", )


class PostLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("id", )


class PostListSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field="email", read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "user",
            "content",
            "created_at",
            "likes_count",
            "comments_count",
            "image",
        )
        ordering = ("created_at",)


class PostDetailSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field="email", read_only=True)
    likes = serializers.SlugRelatedField(
        slug_field="email",
        read_only=True,
        many=True
    )
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    comments = CommentSerializer(read_only=True, many=True)

    class Meta:
        model = Post
        fields = (
            "id", "user", "content", "created_at", "image",
            "likes_count", "likes",
            "comments_count", "comments",
        )
        read_only_fields = ("image", )
