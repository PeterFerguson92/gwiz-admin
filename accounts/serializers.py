# accounts/serializers.py

from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

User = get_user_model()


# ---------------------------------------------------------
# REGISTER SERIALIZER
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# EMAIL LOGIN SERIALIZER
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# GOOGLE LOGIN SERIALIZER
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# PROFILE UPDATE SERIALIZER
# ---------------------------------------------------------
class UserUpdateSerializer(serializers.ModelSerializer):
    # Match your RegisterSerializer naming
    name = serializers.CharField(source="first_name", required=False)
    surname = serializers.CharField(source="last_name", required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "full_name",
            "name",
            "surname",
            "phone_number",
            "avatar_url",
            "is_social_login",
            "provider",
        ]
        read_only_fields = [
            "id",
            "username",
            "full_name",
            "avatar_url",
            "is_social_login",
            "provider",
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

        # If the user logged in through Google (or any social provider),
        # they cannot change their email.
        if self.instance and self.instance.is_social_login:
            if value != self.instance.email:
                raise serializers.ValidationError(
                    "Email cannot be changed for social login accounts."
                )
            return value  # unchanged, allowed

        # ----- Normal account email validation -----

        # Enforce uniqueness, except for the current user
        qs = User.objects.filter(email=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Email is already registered.")

        return value

    def update(self, instance, validated_data):
        """
        Ensure full_name is kept in sync with first_name / last_name.
        validated_data already uses real field names (first_name, last_name, etc.)
        because of `source=`.
        """
        first_name = validated_data.pop("first_name", instance.first_name)
        last_name = validated_data.pop("last_name", instance.last_name)

        instance.first_name = first_name
        instance.last_name = last_name
        instance.full_name = f"{first_name} {last_name}".strip()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

# ---------------------------------------------------------
# CHANGE PASSWORD SERIALIZER
# ---------------------------------------------------------
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if user is None or not user.is_authenticated:
            raise serializers.ValidationError("User is not authenticated.")

        old_password = attrs.get("old_password")
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        # ---- Confirm new passwords match ----
        if new_password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )

        # ---- Social login users: don't require old password ----
        if not user.is_social_login:
            # Only enforce old password for non-social accounts
            if user.has_usable_password():
                if not old_password:
                    raise serializers.ValidationError(
                        {"old_password": "Current password is required."}
                    )
                if not user.check_password(old_password):
                    raise serializers.ValidationError(
                        {"old_password": "Current password is incorrect."}
                    )

        # ---- Validate new password strength ----
        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})

        return attrs

    def save(self, **kwargs):
        request = self.context.get("request")
        user = request.user

        new_password = self.validated_data["new_password"]
        user.set_password(new_password)
        user.save()

        return user
# ---------------------------------------------------------
# RESET PASSWORD SERIALIZERS
# ---------------------------------------------------------    
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # Normalize email
        return value.strip().lower()

    def save(self, **kwargs):
        """
        If a user with this email exists, create a reset token
        and send a reset email. We don't reveal whether the email exists.
        """
        request = self.context.get("request")
        email = self.validated_data["email"]

        user = User.objects.filter(email=email).first()
        if not user:
            # Silently ignore to avoid leaking which emails exist
            return None

        token_generator = PasswordResetTokenGenerator()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        # Build reset URL
        # Prefer frontend route, fall back to backend confirm endpoint
        frontend_url = getattr(settings, "FRONTEND_RESET_PASSWORD_URL", None)
        if frontend_url:
            # e.g. https://app.fsxcg.com/reset-password?uid=...&token=...
            reset_url = f"{frontend_url}?uid={uid}&token={token}"
        else:
            # Fallback to backend endpoint
            path = reverse("auth-password-reset-confirm")
            base_url = request.build_absolute_uri(path) if request else ""
            reset_url = f"{base_url}?uid={uid}&token={token}"

        # Email content
        user_name = user.first_name or user.email

        subject = "Reset your Fsxcg password"
        plain_message = (
            f"Hi {user_name},\n\n"
            "We received a request to reset the password for your account.\n\n"
            f"To reset your password, click the link below:\n\n"
            f"{reset_url}\n\n"
            "If you did not request a password reset, you can safely ignore this email.\n\n"
            "Thanks,\n"
            "The Fsxcg Team"
        )

        html_message = f"""
        <!DOCTYPE html>
        <html>
          <body style="font-family: Arial, sans-serif; background-color:#f6f6f6; padding: 20px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 520px; margin:auto; background:#ffffff; padding: 20px; border-radius: 8px;">
              <tr>
                <td>
                  <h2 style="color:#333333;">Reset Your Password</h2>

                  <p style="font-size: 15px; color:#555;">
                    Hi {user_name},
                  </p>

                  <p style="font-size: 15px; color:#555;">
                    We received a request to reset your password. Click the button below to choose a new one.
                  </p>

                  <p style="text-align:center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background-color:#007bff; color:white; padding:12px 24px; text-decoration:none; border-radius:6px; font-weight:bold;">
                      Reset Password
                    </a>
                  </p>

                  <p style="font-size: 14px; color:#777;">
                    If the button does not work, copy and paste this link into your browser:
                  </p>

                  <p style="font-size: 14px; word-break: break-all; color:#007bff;">
                    {reset_url}
                  </p>

                  <hr style="border:none; border-top:1px solid #eee; margin: 25px 0;"/>

                  <p style="font-size: 13px; color:#999;">
                    If you did not request a password reset, you can safely ignore this email.
                  </p>

                  <p style="font-size: 14px; color:#333;">— The Fsxcg Team</p>
                </td>
              </tr>
            </table>
          </body>
        </html>
        """

        # Send via Django email backend (configured to use SendGrid in settings.py)
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        # Optionally return data for logging/debugging
        return {
            "user": user,
            "uid": uid,
            "token": token,
            "reset_url": reset_url,
        }


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        uid = attrs.get("uid")
        token = attrs.get("token")
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        # 1) Check passwords match
        if new_password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )

        # 2) Resolve user from uid
        try:
            uid_str = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid_str)
        except Exception:
            raise serializers.ValidationError({"uid": "Invalid reset link."})

        # 3) Check token validity
        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, token):
            raise serializers.ValidationError(
                {"token": "Invalid or expired reset token."}
            )

        # 4) Validate new password strength
        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})

        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        new_password = self.validated_data["new_password"]
        user.set_password(new_password)
        user.save()
        return user

# ---------------------------------------------------------
# DOCUMENTATION-ONLY SERIALIZERS
# ---------------------------------------------------------
class UserReadSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="first_name")
    surname = serializers.CharField(source="last_name")

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "name",
            "surname",
            "full_name",
            "avatar_url",
            "phone_number",
            "is_social_login",
            "provider",
        ]


class AuthTokenResponseSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()
    user = UserReadSerializer()


class DetailSerializer(serializers.Serializer):
    detail = serializers.CharField()