from django.urls import path

from .views import (
    ActiveFitnessClassListView,
    AllUpcomingSessionsView,
    BookSessionView,
    CancelBookingView,
    FitnessClassDetailView,
    FitnessClassListView,
    FitnessClassSessionsView,
    FitnessClassWithUpcomingSessionsView,
    MyBookingsListView,
    StripeWebhookView,
    UpcomingClassSessionListView,
)

urlpatterns = [
    # Fitness class list
    path(
        "fitness-classes/",
        FitnessClassListView.as_view(),
        name="fitness-class-list",
    ),
    # Active fitness classes
    path(
        "fitness-classes/active",
        ActiveFitnessClassListView.as_view(),
        name="active-fitness-classes",
    ),
    # All upcoming sessions (global)
    path(
        "sessions/all-upcoming",
        AllUpcomingSessionsView.as_view(),
        name="all-upcoming-sessions",
    ),
    # Upcoming sessions across all classes (date/genre filters)
    path(
        "sessions/upcoming",
        UpcomingClassSessionListView.as_view(),
        name="upcoming-sessions",
    ),
    # Sessions for a specific fitness class
    path(
        "fitness-classes/<uuid:pk>/sessions/",
        FitnessClassSessionsView.as_view(),
        name="fitness-class-sessions",
    ),
    # Booking endpoints
    path(
        "sessions/<uuid:session_id>/book/",
        BookSessionView.as_view(),
        name="book-session",
    ),
    path(
        "bookings/<uuid:booking_id>/cancel/",
        CancelBookingView.as_view(),
        name="cancel-booking",
    ),
    path(
        "my-bookings/",
        MyBookingsListView.as_view(),
        name="my-bookings",
    ),
    # NEW — Get class by ID
    path(
        "fitness-classes/<uuid:pk>/",
        FitnessClassDetailView.as_view(),
        name="fitness-class-detail",
    ),
    # NEW — Get class by ID + upcoming sessions with ?days= parameter
    path(
        "fitness-classes/<uuid:pk>/with-sessions/",
        FitnessClassWithUpcomingSessionsView.as_view(),
        name="fitness-class-with-sessions",
    ),
    path(
        "stripe/webhook/",
        StripeWebhookView.as_view(),
        name="stripe-webhook",
    ),
]
