# accounts/serializers.py

from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    # What user sends in
    name = serializers.CharField(required=True, source="first_name")
    surname = serializers.CharField(required=True, source="last_name")
    email = serializers.EmailField(required=True)
    phone_number = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, min_length=8)

    # What user gets back
    username = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "full_name",
            "name",
            "surname",
            "email",
            "password",
            "phone_number",
        ]

    def validate_phone_number(self, value):
        import re

        value = value.strip()

        pattern = r"^[0-9+\-]+$"
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "Phone number can only contain digits, + and -, and no spaces."
            )

        if len(value) < 7:
            raise serializers.ValidationError("Phone number is too short.")

        if len(value) > 20:
            raise serializers.ValidationError("Phone number is too long.")

        return value

    def validate_email(self, value):
        value = value.strip().lower()

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already registered.")

        return value

    def validate_name(self, value):
        value = value.strip()

        if len(value) < 2:
            raise serializers.ValidationError(
                "Name must be at least 2 characters long."
            )
        if any(char.isdigit() for char in value):
            raise serializers.ValidationError("Name cannot contain numbers.")

        # Auto-capitalize (john → John, mcdoe → Mcdoe)
        return value.title()

    def validate_surname(self, value):
        value = value.strip()

        if len(value) < 2:
            raise serializers.ValidationError(
                "Surname must be at least 2 characters long."
            )
        if any(char.isdigit() for char in value):
            raise serializers.ValidationError("Surname cannot contain numbers.")

        # Auto-capitalize
        return value.title()

    def validate(self, attrs):
        password = attrs.get("password")
        user = User(
            email=attrs.get("email"),
            first_name=attrs.get("first_name"),
            last_name=attrs.get("last_name"),
        )
        try:
            validate_password(password, user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        first_name = validated_data.pop("first_name").strip()
        last_name = validated_data.pop("last_name").strip()

        full_name = f"{first_name} {last_name}".strip()

        email = validated_data.get("email")
        phone_number = validated_data.get("phone_number")

        # Base username from name + surname
        base_username = slugify(f"{first_name}.{last_name}") or slugify(
            email.split("@")[0]
        )
        if not base_username:
            base_username = "user"

        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            counter += 1
            username = f"{base_username}{counter}"

        user = User(
            username=username,
            email=email,
            phone_number=phone_number,
            full_name=full_name,
            first_name=first_name,
            last_name=last_name,
            is_social_login=False,
            provider="",
        )
        user.set_password(password)
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
                "name": user.first_name,
                "surname": user.last_name,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "phone_number": user.phone_number,
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
                {"id_token": f"Google token verification failed: {e}"}
            )

        email = idinfo.get("email")
        if not email:
            raise serializers.ValidationError({"id_token": "Google token has no email"})

        full_name = idinfo.get("name") or ""
        avatar_url = idinfo.get("picture") or ""
        given_name = idinfo.get("given_name") or ""
        family_name = idinfo.get("family_name") or ""

        # Get or create the user by email
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "full_name": full_name,
                "avatar_url": avatar_url,
                "first_name": given_name,
                "last_name": family_name,
                "is_social_login": True,
                "provider": "google",
                # NOTE: phone_number intentionally omitted; we don't get it from Google
            },
        )

        # If user existed already, update social fields if needed
        changed = False
        if full_name and user.full_name != full_name:
            user.full_name = full_name
            changed = True
        if given_name and user.first_name != given_name:
            user.first_name = given_name
            changed = True
        if family_name and user.last_name != family_name:
            user.last_name = family_name
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
                "name": user.first_name,
                "surname": user.last_name,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "phone_number": user.phone_number,
                "is_social_login": user.is_social_login,
                "provider": user.provider,
            },
        }
