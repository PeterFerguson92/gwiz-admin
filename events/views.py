import datetime
import logging

import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from booking import membership
from booking.tokens import generate_cancel_token, verify_cancel_token

from . import payments
from .email_utils import send_ticket_cancellation_email, send_ticket_confirmation_email
from .models import Event, EventTicket
from .serializer import (
    EventSerializer,
    EventTicketSerializer,
    PurchaseRequestSerializer,
)

logger = logging.getLogger(__name__)


class UpcomingEventListView(generics.ListAPIView):
    """
    Public list of active, not-sold-out events. Defaults to upcoming only.
    """

    serializer_class = EventSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        today = datetime.date.today()
        qs = Event.objects.filter(is_active=True, start_datetime__date__gte=today)

        # optional: include past with ?include_past=1
        include_past = self.request.query_params.get("include_past")
        if include_past and include_past.lower() in ("1", "true", "yes"):
            qs = Event.objects.filter(is_active=True)

        return qs.order_by("-is_featured", "featured_order", "start_datetime", "name")


class ActiveEventListView(generics.ListAPIView):
    """
    Public list of all active events (no date filter).
    """

    serializer_class = EventSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Event.objects.filter(is_active=True).order_by(
            "-is_featured", "featured_order", "start_datetime", "name"
        )


class EventDetailView(generics.RetrieveAPIView):
    serializer_class = EventSerializer
    permission_classes = [AllowAny]
    queryset = Event.objects.filter(is_active=True)


@extend_schema(
    tags=["Events"],
    request=PurchaseRequestSerializer,
    responses={201: EventTicketSerializer},
)
class PurchaseTicketView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, event_id):
        user = request.user if request.user.is_authenticated else None
        guest_name = request.data.get("guest_name", "").strip()
        guest_email = request.data.get("guest_email", "").strip()
        guest_phone = request.data.get("guest_phone", "").strip()

        payload = PurchaseRequestSerializer(data=request.data or {})
        payload.is_valid(raise_exception=True)
        quantity = payload.validated_data["quantity"]

        with transaction.atomic():
            event = (
                Event.objects.select_for_update()
                .filter(id=event_id, is_active=True)
                .first()
            )
            if not event:
                return Response(
                    {"detail": "Event not found or inactive."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # block past events
            if event.start_datetime < timezone.now():
                return Response(
                    {"detail": "This event has already started."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if quantity > event.remaining_tickets:
                return Response(
                    {"detail": "Not enough tickets available."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if user:
                existing = EventTicket.objects.filter(
                    user=user,
                    event=event,
                    status__in=EventTicket.ACTIVE_STATUSES,
                ).first()
                if existing:
                    return Response(
                        {"detail": "You already have an active ticket for this event."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                if not guest_email:
                    return Response(
                        {"detail": "guest_email is required for guest tickets."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            can_use_membership = False
            if user:
                can_use_membership, membership_reason = membership.can_book_event(
                    user, event, n=quantity
                )
            use_membership = bool(can_use_membership)

            is_free = event.ticket_price == 0 or use_membership
            payment_status = (
                EventTicket.PAYMENT_INCLUDED if is_free else EventTicket.PAYMENT_PENDING
            )
            status_value = (
                EventTicket.STATUS_CONFIRMED if is_free else EventTicket.STATUS_RESERVED
            )

            ticket = EventTicket.objects.create(
                user=user,
                guest_name=guest_name,
                guest_email=guest_email,
                guest_phone=guest_phone,
                is_guest_purchase=user is None,
                event=event,
                quantity=quantity,
                status=status_value,
                payment_status=payment_status,
            )

        client_secret = None
        cancel_token = None

        if not is_free:
            try:
                intent = payments.create_payment_intent_for_ticket(ticket)
            except ImproperlyConfigured:
                logger.exception(
                    "Stripe is not configured; deleting ticket %s", ticket.id
                )
                ticket.delete()
                return Response(
                    {"detail": "Online payments are currently unavailable."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            except ValueError as exc:
                logger.exception(
                    "Invalid payment configuration for ticket %s: %s", ticket.id, exc
                )
                ticket.delete()
                return Response(
                    {"detail": str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except stripe.error.StripeError as exc:
                logger.exception(
                    "Stripe error while creating PaymentIntent for ticket %s: %s",
                    ticket.id,
                    exc,
                )
                ticket.delete()
                return Response(
                    {"detail": "Unable to start payment. Please try again."},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            ticket.stripe_payment_intent_id = intent.id
            ticket.save(update_fields=["stripe_payment_intent_id", "updated_at"])
            client_secret = intent.client_secret
        else:
            # Free or membership-included tickets confirm immediately; consume credits when needed
            if use_membership:
                membership.consume_event_credit(
                    user, event, n=quantity, reference_id=ticket.id
                )
            cancel_token = (
                None if user else generate_cancel_token("event_ticket", ticket.id)
            )
            send_ticket_confirmation_email(ticket, cancel_token=cancel_token)

        serializer = EventTicketSerializer(ticket)
        data = serializer.data
        if client_secret:
            data["stripe_client_secret"] = client_secret
        if is_free:
            data["email_sent"] = True
        if user is None:
            if cancel_token is None:
                cancel_token = generate_cancel_token("event_ticket", ticket.id)
            data["cancel_token"] = cancel_token

        return Response(data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Events"], responses=EventTicketSerializer(many=True))
class MyTicketsListView(generics.ListAPIView):
    serializer_class = EventTicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            EventTicket.objects.filter(user=self.request.user)
            .select_related("event")
            .order_by("-created_at")
        )


@extend_schema(tags=["Events"], responses=EventTicketSerializer)
class CancelTicketView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, ticket_id):
        user = request.user if request.user.is_authenticated else None
        ticket = (
            EventTicket.objects.select_related("event").filter(id=ticket_id).first()
        )

        if not ticket:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if ticket.status == EventTicket.STATUS_CANCELLED:
            return Response(
                {"detail": "Ticket is already cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Authenticated path: must own ticket
        if user:
            if ticket.user_id != user.id:
                return Response(
                    {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Guest path: require token
            token = request.data.get("token") or request.query_params.get("token") or ""
            if not token or not verify_cancel_token(token, "event_ticket", ticket_id):
                return Response(
                    {"detail": "Invalid or missing cancel token."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if ticket.user_id is not None:
                return Response(
                    {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
                )

        # Only allow cancellation before event start
        if ticket.event.start_datetime < timezone.now():
            return Response(
                {"detail": "Event has already started."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment_status_changed = False
        if ticket.payment_status == EventTicket.PAYMENT_PENDING:
            ticket.payment_status = EventTicket.PAYMENT_VOID
            payment_status_changed = True
        elif ticket.payment_status == EventTicket.PAYMENT_PAID:
            # Attempt refund; failures are logged but do not block cancellation
            payments.refund_payment_intent(ticket.stripe_payment_intent_id)
            ticket.payment_status = EventTicket.PAYMENT_VOID
            payment_status_changed = True

        ticket.status = EventTicket.STATUS_CANCELLED
        update_fields = ["status", "updated_at"]
        if payment_status_changed:
            update_fields.append("payment_status")
        ticket.save(update_fields=update_fields)
        if ticket.payment_status == EventTicket.PAYMENT_INCLUDED:
            membership.restore_event_credit(
                user, ticket.event, n=ticket.quantity, reference_id=ticket.id
            )
        cancel_email_sent = send_ticket_cancellation_email(ticket)
        logger.info(
            "Ticket %s cancelled by user; email_sent=%s",
            ticket.id,
            cancel_email_sent,
        )

        serializer = EventTicketSerializer(ticket)
        data = serializer.data
        data["cancellation_email_sent"] = cancel_email_sent
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Events"],
    auth=[],
    request=None,
    responses={200: OpenApiTypes.OBJECT},
)
class StripeWebhookView(APIView):
    """
    Receives Stripe webhooks to update ticket payment states.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

        try:
            event = payments.parse_stripe_event(request.body, sig_header)
        except ValueError:
            logger.warning("Stripe webhook received invalid JSON payload.")
            return Response(
                {"detail": "Invalid payload."}, status=status.HTTP_400_BAD_REQUEST
            )
        except stripe.error.SignatureVerificationError:
            logger.warning("Stripe webhook signature verification failed.")
            return Response(
                {"detail": "Invalid Stripe signature."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ImproperlyConfigured:
            logger.error("Stripe webhook invoked but STRIPE_SECRET_KEY is missing.")
            return Response(
                {"detail": "Stripe webhook is not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})

        if not data:
            logger.warning(
                "Stripe webhook missing data.object for event %s", event_type
            )
            return Response(
                {"detail": "Event payload missing data."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if event_type == "payment_intent.succeeded":
            self._handle_payment_intent_succeeded(data)
        elif event_type in ("payment_intent.payment_failed", "payment_intent.canceled"):
            self._handle_payment_intent_failed(data)
        else:
            logger.debug("Ignoring Stripe event type %s", event_type)

        return Response({"received": True}, status=status.HTTP_200_OK)

    def _handle_payment_intent_succeeded(self, payload: dict) -> None:
        intent_id = payload.get("id")
        if not intent_id:
            logger.warning("Stripe event missing PaymentIntent id for success handler.")
            return

        ticket = EventTicket.objects.filter(stripe_payment_intent_id=intent_id).first()

        if not ticket:
            logger.warning(
                "Stripe PaymentIntent %s was successful but no ticket matched.",
                intent_id,
            )
            return

        if ticket.payment_status == EventTicket.PAYMENT_PAID:
            return

        ticket.payment_status = EventTicket.PAYMENT_PAID
        ticket.status = EventTicket.STATUS_CONFIRMED
        ticket.save(update_fields=["payment_status", "status", "updated_at"])
        cancel_token = None
        if ticket.user_id is None:
            cancel_token = generate_cancel_token("event_ticket", ticket.id)
        email_sent = send_ticket_confirmation_email(ticket, cancel_token=cancel_token)
        logger.info(
            "Marked ticket %s as paid from Stripe webhook; email_sent=%s",
            ticket.id,
            email_sent,
        )

    def _handle_payment_intent_failed(self, payload: dict) -> None:
        intent_id = payload.get("id")
        if not intent_id:
            logger.warning("Stripe event missing PaymentIntent id for failure handler.")
            return

        ticket = EventTicket.objects.filter(stripe_payment_intent_id=intent_id).first()

        if not ticket:
            logger.warning(
                "Stripe PaymentIntent %s failed but no ticket matched.",
                intent_id,
            )
            return

        changed_fields = []
        if ticket.status != EventTicket.STATUS_CANCELLED:
            ticket.status = EventTicket.STATUS_CANCELLED
            changed_fields.append("status")
        if ticket.payment_status != EventTicket.PAYMENT_VOID:
            ticket.payment_status = EventTicket.PAYMENT_VOID
            changed_fields.append("payment_status")

        if changed_fields:
            changed_fields.append("updated_at")
            ticket.save(update_fields=changed_fields)
            if ticket.payment_status == EventTicket.PAYMENT_INCLUDED:
                membership.restore_event_credit(
                    ticket.user, ticket.event, n=ticket.quantity, reference_id=ticket.id
                )
            email_sent = send_ticket_cancellation_email(ticket)
            logger.info(
                "Marked ticket %s as cancelled/void due to failed Stripe payment; email_sent=%s",
                ticket.id,
                email_sent,
            )
