import pathlib
import uuid

from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext as _

from django.contrib.auth.models import AbstractUser

from user.managers import UserManager


def set_filename(new_filename, filename: str) -> pathlib.Path:
    return (f"{slugify(new_filename)}-{uuid.uuid4()}"
            + pathlib.Path(filename).suffix)


def profile_picture_path(instance, filename: str) -> pathlib.Path:
    return pathlib.Path(
        "upload/" + instance.__class__.__name__.lower()
    ) / pathlib.Path(
        set_filename(instance.full_name + "-" + instance.email, filename)
    )


class User(AbstractUser):
    username = None
    email = models.EmailField(_("email address"), unique=True, db_index=True)
    bio = models.TextField(_("bio"), blank=True)
    location = models.CharField(max_length=255, blank=True)
    profile_picture = models.ImageField(
        null=True,
        blank=True,
        upload_to=profile_picture_path
    )
    followers = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="followed_by",
        blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.email
