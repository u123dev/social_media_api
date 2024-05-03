from django.urls import path, include
from rest_framework import routers

from social_media.views import UserProfileViewSet

app_name = "social_media"

router = routers.DefaultRouter()
router.register("profiles", UserProfileViewSet, basename="profiles")

urlpatterns = [
    path("", include(router.urls)),
]
