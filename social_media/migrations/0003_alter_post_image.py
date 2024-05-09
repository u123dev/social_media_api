# Generated by Django 5.0.4 on 2024-05-09 20:54

import social_media.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("social_media", "0002_alter_comment_post_alter_comment_user"),
    ]

    operations = [
        migrations.AlterField(
            model_name="post",
            name="image",
            field=models.ImageField(
                blank=True, null=True, upload_to=social_media.models.post_picture_path
            ),
        ),
    ]
