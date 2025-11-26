from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import EmailTokenObtainPairView, RegisterView, MeView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    # path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),  login with username
    path("token/", EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),

]