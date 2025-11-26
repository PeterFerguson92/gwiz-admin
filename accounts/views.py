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
from .serializers import EmailTokenObtainSerializer, RegisterSerializer

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
    GET /api/auth/me/
    Returns basic info about the currently authenticated user.
    Requires Authorization: Bearer <access_token>.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                "id": user.id,
                "email": user.email,
                "username": user.username,
            }
        )