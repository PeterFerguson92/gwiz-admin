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
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    GoogleLoginSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
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
    
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password updated successfully."})
    
class PasswordResetRequestView(APIView):
    """
    POST /api/auth/password/reset/
    Body: { "email": "<user-email>" }

    Always returns a generic success message, even if the email
    is not registered, to avoid leaking which emails exist.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        # For debugging you *could* return uid/token here,
        # but in production you normally just email them.
        # Example debug:
        # if settings.DEBUG and result:
        #     return Response({
        #         "detail": "Password reset email sent.",
        #         "uid": result["uid"],
        #         "token": result["token"],
        #     })

        return Response(
            {
                "detail": "If an account with that email exists, we have sent password reset instructions."
            }
        )


class PasswordResetConfirmView(APIView):
    """
    POST /api/auth/password/reset/confirm/
    Body:
    {
      "uid": "<uid-from-link>",
      "token": "<token-from-link>",
      "new_password": "...",
      "confirm_password": "..."
    }
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password has been reset successfully."})

