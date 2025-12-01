from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # Make email required & unique for login
    email = models.EmailField(unique=True)

    # Extra profile fields
    full_name = models.CharField(max_length=255, blank=True)
    avatar_url = models.URLField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

    # Social login flags
    is_social_login = models.BooleanField(default=False)
    provider = models.CharField(
        max_length=50,
        blank=True,  # e.g. "google", "facebook"
        help_text="Authentication provider for social logins.",
    )

    # You can add more fields later, e.g.:
    # is_instructor = models.BooleanField(default=False)

    def __str__(self):
        return self.email or self.username
