from django.urls import path

from .views import (
    ActiveEventListView,
    CancelTicketView,
    EventDetailView,
    MyTicketsListView,
    PurchaseTicketView,
    StripeWebhookView,
    TicketCheckInView,
    TicketRevertCheckInView,
    UpcomingEventListView,
)

urlpatterns = [
    path("", UpcomingEventListView.as_view(), name="event-list"),
    path("active/", ActiveEventListView.as_view(), name="active-event-list"),
    path("<uuid:pk>/", EventDetailView.as_view(), name="event-detail"),
    path(
        "<uuid:event_id>/tickets/",
        PurchaseTicketView.as_view(),
        name="event-purchase",
    ),
    path("tickets/my/", MyTicketsListView.as_view(), name="my-event-tickets"),
    path(
        "tickets/<uuid:ticket_id>/cancel/",
        CancelTicketView.as_view(),
        name="cancel-event-ticket",
    ),
    path(
        "tickets/<uuid:ticket_id>/check-in/",
        TicketCheckInView.as_view(),
        name="event-ticket-check-in",
    ),
    path(
        "tickets/<uuid:ticket_id>/revert-check-in/",
        TicketRevertCheckInView.as_view(),
        name="event-ticket-revert-check-in",
    ),
    path("stripe/webhook/", StripeWebhookView.as_view(), name="event-stripe-webhook"),
]
