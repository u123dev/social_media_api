import os
import tempfile

from PIL import Image
from django.db.models import Q
from django.test import TestCase

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from social_media.serializers import (
    UserProfileListSerializer,
    UserProfileDetailSerializer,
    UserFollowSerializer
)
from social_media.tests.init_sample import init_sample_user

PROFILE_URL = reverse("social_media:profiles-list")
PROFILE_DETAIL = "social_media:profiles-detail"
PROFILE_FOLLOW = "social_media:profiles-follow"
PROFILE_UNFOLLOW = "social_media:profiles-unfollow"
PROFILE_FOLLOWERS = "social_media:profiles-get-followers"
PROFILE_FOLLOWED_BY = "social_media:profiles-get-followed-by"
PROFILE_PICTURE = "social_media:profiles-set-picture"


def detail_url(url, instance_id):
    return reverse(url, args=[instance_id])


class AuthenticatedProfileApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = init_sample_user(1)
        self.client.force_authenticate(self.user1)
        self.user2 = init_sample_user(2)
        self.user3 = init_sample_user(3)

    def test_list_profiles(self):
        res = self.client.get(PROFILE_URL)

        profiles = get_user_model().objects.all()
        serializer = UserProfileListSerializer(profiles, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for num, data in enumerate(serializer.data):
            for key, value in data.items():
                self.assertEqual(res.data[num][key], value)

    def test_filter_list_profiles(self):
        self.user22 = init_sample_user(22)
        res = self.client.get(PROFILE_URL, {"name": "2"})

        profiles = get_user_model().objects.filter(
            Q(email__icontains="2")
            | Q(first_name__icontains="2")
            | Q(last_name__icontains="2")
        )

        serializer = UserProfileListSerializer(profiles, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for num, data in enumerate(serializer.data):
            for key, value in data.items():
                self.assertEqual(res.data[num][key], value)

    def test_retrieve_profile_detail(self):
        res = self.client.get(detail_url(PROFILE_DETAIL, self.user1.id))

        serializer1 = UserProfileDetailSerializer(self.user1)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        for key, value in serializer1.data.items():
            self.assertEqual(res.data[key], value)

    def test_follow_unfollow_profile(self):
        res = self.client.post(detail_url(PROFILE_FOLLOW, self.user2.id))

        serializer2 = UserProfileDetailSerializer(self.user2)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(self.user1.email, serializer2.data.get("followers"))

        res = self.client.post(detail_url(PROFILE_UNFOLLOW, self.user2.id))

        serializer2 = UserProfileDetailSerializer(self.user2)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.user1.email, serializer2.data.get("followers"))

    def test_list_followers_profile(self):
        res = self.client.post(detail_url(PROFILE_FOLLOW, self.user2.id))

        self.client.force_authenticate(self.user3)
        res = self.client.post(detail_url(PROFILE_FOLLOW, self.user2.id))

        res = self.client.get(detail_url(PROFILE_FOLLOWERS, self.user2.id))
        serializer2 = UserFollowSerializer(self.user2.followers.all(), many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer2.data)

    def test_list_followed_by_profile(self):
        res = self.client.post(detail_url(PROFILE_FOLLOW, self.user2.id))
        res = self.client.post(detail_url(PROFILE_FOLLOW, self.user3.id))

        res = self.client.get(detail_url(PROFILE_FOLLOWED_BY, self.user1.id))
        serializer1 = UserFollowSerializer(self.user1.followed_by.all(), many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer1.data)


class ProfilePhotoUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = init_sample_user(1)
        self.client.force_authenticate(self.user1)
        self.user2 = init_sample_user(2)

    def tearDown(self):
        self.user1.profile_picture.delete()

    def test_upload_profile_picture(self):
        """Test uploading profile picture"""
        url = detail_url(PROFILE_PICTURE, self.user1.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"profile_picture": ntf}, format="multipart")
        self.user1.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("profile_picture", res.data)
        self.assertTrue(os.path.exists(self.user1.profile_picture.path))

    def test_upload_profile_picture_another_user_forbidden(self):
        """Test uploading profile picture for another user is forbidden """
        url = detail_url(PROFILE_PICTURE, self.user2.id)
        res = self.client.post(url, {"profile_picture": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
