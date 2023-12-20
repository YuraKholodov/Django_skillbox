from django.contrib.auth.models import User
from django.db import models


def profile_avatar_directory_path(instanse: "Profile", filename: str) -> str:
    return f"profiles/profile_{instanse.pk}/{filename}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    agreement_accepted = models.BooleanField(default=False)
    avatar = models.ImageField(null=True, blank=True, upload_to=profile_avatar_directory_path)
