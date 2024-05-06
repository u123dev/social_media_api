from django.db import models

from social_media_api import settings
from user.models import User


class Post(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="upload/post", null=True, blank=True)
    likes = models.ManyToManyField(User, related_name='likes', blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"post id={self.id} | {self.created_at} | {self.content[:15]} ..."


class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"comment id={self.id} | {self.created_at} | {self.message[:15]}"
