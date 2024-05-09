from django.urls import path, include
from rest_framework import routers

from social_media.views import UserProfileViewSet, PostViewSet, CommentViewSet

app_name = "social_media"

router = routers.DefaultRouter()
router.register("profiles", UserProfileViewSet, basename="profiles")
router.register("posts", PostViewSet, basename="posts")
router.register("comments", CommentViewSet, basename="comments")

urlpatterns = [
    path("", include(router.urls)),
]
