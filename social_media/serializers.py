from django.contrib.auth import get_user_model
from rest_framework import serializers


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
