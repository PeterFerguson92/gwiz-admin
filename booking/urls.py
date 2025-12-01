from django.urls import path

from .views import (
    ActiveFitnessClassListView,
    AllUpcomingSessionsView,
    FitnessClassListView,
    FitnessClassSessionsView,
    UpcomingClassSessionListView,
)

urlpatterns = [
    path("fitness-classes/", FitnessClassListView.as_view(), name="fitness-class-list"),
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
    path(
        "sessions/all-upcoming",
        AllUpcomingSessionsView.as_view(),
        name="all-upcoming-sessions",
    ),
    path(
        "fitness-classes/<uuid:pk>/sessions/",
        FitnessClassSessionsView.as_view(),
        name="fitness-class-sessions",
    ),
]
