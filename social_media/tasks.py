import base64
import io
import os

from PIL import Image
from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.files import File


from social_media.models import Post


@shared_task
def publish_post(content, image_data, user_id):

    creator = get_user_model().objects.get(pk=user_id)

    if image_data:
        byte_data = image_data['image'].encode(encoding='utf-8')
        b = base64.b64decode(byte_data)
        img = Image.open(io.BytesIO(b))
        img.save(image_data['name'], format=img.format)

        with open(image_data['name'], 'rb') as file:
            picture = File(file)
            post = Post.objects.create(
                content=content,
                image=picture,
                user=creator,
            )
        os.remove(image_data['name'])
    else:
        post = Post.objects.create(
            content=content,
            image=None,
            user=creator,
        )
    result = f"Post #{post.pk} added"
    print(result)
    return result
