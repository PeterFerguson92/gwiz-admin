from django.urls import path

from attendance.views import CheckInByTokenView

urlpatterns = [
    path(
        "check-in/by-token/",
        CheckInByTokenView.as_view(),
        name="staff-check-in-by-token",
    ),
]
