from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # Make email required & unique for login
    email = models.EmailField(unique=True)

    # You can add more fields later, e.g.:
    # is_instructor = models.BooleanField(default=False)

    def __str__(self):
        return self.email or self.username
