# accounts/serializers.py

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Register a new user with email, username and password.
    Non-social users: is_social_login=False, provider="".
    """
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "full_name"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        full_name = validated_data.get("full_name") or ""

        user = User(
            **validated_data,
            full_name=full_name,
            is_social_login=False,
            provider="",  # local/email-password user
        )
        user.set_password(password)  # hashes the password
        user.save()
        return user


class EmailTokenObtainSerializer(TokenObtainPairSerializer):
    """
    JWT login using email + password.
    Returns refresh, access and user info.
    """

    username_field = User.EMAIL_FIELD  # "email"

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if not email or not password:
            raise serializers.ValidationError("Email and password are required")

        user = User.objects.filter(email=email).first()

        if user is None or not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password")

        token = self.get_token(user)

        data = {
            "refresh": str(token),
            "access": str(token.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "is_social_login": user.is_social_login,
                "provider": user.provider,
            },
        }

        return data


class GoogleLoginSerializer(serializers.Serializer):
    """
    Accepts a Google ID token, verifies it, and returns JWT tokens + user info.
    Also sets:
      - is_social_login = True
      - provider = "google"
      - full_name, avatar_url from Google profile
    """

    id_token = serializers.CharField(write_only=True)

    def validate(self, attrs):
        id_token_str = attrs.get("id_token")

        try:
            idinfo = google_id_token.verify_oauth2_token(
                id_token_str,
                google_requests.Request(),
                settings.GOOGLE_OAUTH_CLIENT_ID,
            )
        except Exception as e:
            raise serializers.ValidationError(
                f"Google token verification failed: {e}"
            )

        email = idinfo.get("email")
        if not email:
            raise serializers.ValidationError("Google token has no email")

        full_name = idinfo.get("name") or ""
        avatar_url = idinfo.get("picture") or ""

        # Get or create the user by email
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "full_name": full_name,
                "avatar_url": avatar_url,
                "is_social_login": True,
                "provider": "google",
            },
        )

        # If user existed already, update social fields if needed
        changed = False
        if full_name and user.full_name != full_name:
            user.full_name = full_name
            changed = True
        if avatar_url and user.avatar_url != avatar_url:
            user.avatar_url = avatar_url
            changed = True
        if not user.is_social_login:
            user.is_social_login = True
            changed = True
        if not user.provider:
            user.provider = "google"
            changed = True

        if changed:
            user.save()

        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "is_social_login": user.is_social_login,
                "provider": user.provider,
            },
        }
