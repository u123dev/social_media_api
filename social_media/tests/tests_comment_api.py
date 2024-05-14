import os
import tempfile

from PIL import Image
from django.db.models import Q
from django.test import TestCase

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from social_media.models import Comment
from social_media.serializers import CommentSerializer
from social_media.tests.init_sample import (
    init_sample_user,
    init_sample_post,
    init_sample_comment
)

COMMENT_URL = reverse("social_media:comments-list")


def detail_url(url, instance_id):
    return reverse(url, args=[instance_id])


class AuthenticatedCommentApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = init_sample_user(1)
        self.post1 = init_sample_post(user=self.user1, content="test-post1")
        self.comment1 = init_sample_comment(user=self.user1, post=self.post1, message="comm1")
        self.client.force_authenticate(self.user1)
        self.user2 = init_sample_user(2)
        self.post2 = init_sample_post(user=self.user2, content="test-post2")
        self.comment2 = init_sample_comment(user=self.user1, post=self.post2, message="comm2")

    def test_list_comments(self):
        res = self.client.get(COMMENT_URL)

        comments = Comment.objects.filter(user=self.user1).order_by("-created_at")
        serializer = CommentSerializer(comments, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
