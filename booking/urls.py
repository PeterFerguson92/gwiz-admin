from django.urls import path

from .views import ActiveFitnessClassListView, UpcomingClassSessionListView

urlpatterns = [
    path(
        "sessions/upcoming",
        UpcomingClassSessionListView.as_view(),
        name="upcoming-sessions",
    ),
    path(
        "fitness-classes/active",
        ActiveFitnessClassListView.as_view(),
        name="active-fitness-classes",
    ),
]
