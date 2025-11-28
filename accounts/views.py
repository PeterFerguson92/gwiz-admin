# Create your views here.
from urllib import response
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .serializers import (
    EmailTokenObtainSerializer,
    RegisterSerializer,
    GoogleLoginSerializer,
    UserUpdateSerializer
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]  # open to non-authenticated


class EmailTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/auth/token/
    Logs in using email + password and returns:
      - refresh token
      - access token
      - user info
    """

    serializer_class = EmailTokenObtainSerializer
    permission_classes = [permissions.AllowAny]


class SimpleTokenRefreshView(TokenRefreshView):
    """
    POST /api/auth/token/refresh/
    Takes a refresh token and returns a new access token.
    Body: { "refresh": "<refresh_token>" }
    """

    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    """
    GET    /api/auth/me/      -> return current user profile
    PATCH  /api/auth/me/      -> partial update (name, surname, phone_number, email)
    PUT    /api/auth/me/      -> full update
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserUpdateSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserUpdateSerializer(user).data)

    def put(self, request):
        serializer = UserUpdateSerializer(
            request.user, data=request.data, partial=False
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserUpdateSerializer(user).data)


class GoogleLoginView(APIView):
    """
    POST /api/auth/google/
    Body: { "id_token": "<google_id_token>" }
    Returns: { refresh, access, user }
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 👇 IMPORTANT: use validated_data (what validate() returns)
        return Response(serializer.validated_data)
