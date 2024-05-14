import os
import tempfile

from PIL import Image
from django.db.models import Q
from django.test import TestCase

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from social_media.models import Post, Comment
from social_media.serializers import (
    PostListSerializer,
    PostDetailSerializer,
    CommentSerializer
)
from social_media.tests.init_sample import init_sample_user, init_sample_post

POST_URL = reverse("social_media:posts-list")
POST_DETAIL = "social_media:posts-detail"
POST_ADD_COMMENT = "social_media:posts-comment"
POST_LIKE = "social_media:posts-like"
POST_UNLIKE = "social_media:posts-unlike"
POST_LIST_LIKED = reverse("social_media:posts-liked-posts")
POST_IMAGE = "social_media:posts-image"


def detail_url(url, instance_id):
    return reverse(url, args=[instance_id])


class AuthenticatedPostApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = init_sample_user(1)
        self.post1 = init_sample_post(user=self.user1)
        self.client.force_authenticate(self.user1)
        self.user2 = init_sample_user(2)
        self.user3 = init_sample_user(3)

    def test_list_posts(self):
        self.post2 = init_sample_post(user=self.user1)

        res = self.client.get(POST_URL)

        posts = Post.objects.filter(Q(user=self.user1)).order_by("created_at")
        serializer = PostListSerializer(posts, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for num, data in enumerate(serializer.data):
            for key, value in data.items():
                self.assertEqual(res.data.get("results")[num][key], value)

    def test_filter_list_posts(self):
        self.post2 = init_sample_post(user=self.user1, content="test-lookup-123")
        self.post3 = init_sample_post(user=self.user3, content="test-lookup-456")

        res = self.client.get(POST_URL, {"tag": "lookup"})

        posts = Post.objects.filter(content__icontains="2")
        serializer = PostListSerializer(posts, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for num, data in enumerate(serializer.data):
            for key, value in data.items():
                self.assertEqual(res.data.get("results")[num][key], value)

    def test_retrieve_post_detail(self):
        res = self.client.get(detail_url(POST_DETAIL, self.post1.id))

        serializer1 = PostDetailSerializer(self.post1)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        for key, value in serializer1.data.items():
            self.assertEqual(res.data[key], value)

    def test_add_comment_to_post(self):
        self.post2 = init_sample_post(user=self.user1, content="test-post2")

        payload = {"message": "comment1", "user": self.user1, "post": self.post2}
        res = self.client.post(detail_url(POST_ADD_COMMENT, self.post2.id), payload)

        self.comment = Comment.objects.get(id=res.data["id"])
        serializer1 = CommentSerializer(self.comment)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        for key, value in serializer1.data.items():
            self.assertEqual(str(res.data[key]), str(value))

    def test_like_unlike_posts(self):
        self.post2 = init_sample_post(user=self.user2, content="test-post2")
        # like
        res = self.client.post(detail_url(POST_LIKE, self.post2.id))
        self.post2.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIn(self.user1, self.post2.likes.all())

        # unlike
        res = self.client.post(detail_url(POST_UNLIKE, self.post2.id))
        self.post2.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNotIn(self.user1, self.post2.likes.all())

    def test_list_liked_posts(self):
        self.post2 = init_sample_post(user=self.user2, content="test-post2")
        # like1
        res = self.client.post(detail_url(POST_LIKE, self.post2.id))

        self.post3 = init_sample_post(user=self.user3, content="test-post3")
        # like2
        res = self.client.post(detail_url(POST_LIKE, self.post3.id))

        res = self.client.get(POST_LIST_LIKED)

        posts = Post.objects.filter(likes=self.user1)
        serializer = PostListSerializer(posts, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

class PostImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = init_sample_user(1)
        self.client.force_authenticate(self.user1)
        self.post1 = init_sample_post(user=self.user1, content="test-post1")
        self.user2 = init_sample_user(2)
        self.post2 = init_sample_post(user=self.user2, content="test-post2")

    def tearDown(self):
        self.post1.image.delete()

    def test_upload_post_image(self):
        """Test uploading post image"""
        url = detail_url(POST_IMAGE, self.post1.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.post1.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.post1.image.path))

    def test_upload_profile_picture_another_user_forbidden(self):
        """Test uploading post image for another user's post is forbidden """
        url = detail_url(POST_IMAGE, self.post2.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
