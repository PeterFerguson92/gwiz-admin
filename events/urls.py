from django.urls import path

from .views import (
    CancelTicketView,
    EventDetailView,
    MyTicketsListView,
    PurchaseTicketView,
    StripeWebhookView,
    UpcomingEventListView,
)

urlpatterns = [
    path("", UpcomingEventListView.as_view(), name="event-list"),
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
    path("stripe/webhook/", StripeWebhookView.as_view(), name="event-stripe-webhook"),
]
