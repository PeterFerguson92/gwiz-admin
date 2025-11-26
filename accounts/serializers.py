from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

# ------------------------
# 1. REGISTER SERIALIZER
# ------------------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


# ------------------------
# 2. LOGIN SERIALIZER (email-based JWT)
# ------------------------
class EmailTokenObtainSerializer(TokenObtainPairSerializer):
    """
    Custom JWT login serializer that uses email instead of username.
    It returns:
      - refresh token
      - access token
      - basic user info
    """

    # Tell SimpleJWT that our "username" field conceptually is email
    username_field = User.EMAIL_FIELD  # usually "email"

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if not email or not password:
            raise serializers.ValidationError("Email and password are required")

        # Look up the user by email
        user = User.objects.filter(email=email).first()

        # Check user exists and password matches
        if user is None or not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password")

        # Generate tokens for this user
        token = self.get_token(user)

        data = {
            "refresh": str(token),
            "access": str(token.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
            },
        }

        return data