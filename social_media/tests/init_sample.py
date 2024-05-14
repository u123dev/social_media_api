from django.contrib.auth import get_user_model

from social_media.models import Post, Comment


def init_sample_user(number: int):
    return get_user_model().objects.create_user(
        email=f"test-{str(number)}@test.com",
        password="testpass",
    )

def init_sample_post(**params):
    defaults = {"content": "Sample post", }
    defaults.update(params)
    return Post.objects.create(**defaults)

def init_sample_comment(**params):
    defaults = {"message": "Sample comment", }
    defaults.update(params)
    return Comment.objects.get_or_create(**defaults)[0]
