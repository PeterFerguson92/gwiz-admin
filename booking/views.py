import datetime
import logging

import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Case, Count, ExpressionWrapper, F, IntegerField, Q, When
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from booking.email_utils import send_booking_confirmation_email
from booking.serializer import (
    BookingSerializer,
    ClassSessionSerializer,
    FitnessClassSerializer,
    FitnessClassWithUpcomingSessionsSerializer,
    MembershipPlanSerializer,
    MyBookingSerializer,
    UserMembershipSerializer,
)
from notifications import whatsapp

from . import membership, payments
from .models import (
    Booking,
    ClassSession,
    FitnessClass,
    MembershipPlan,
    MembershipPurchase,
    UserMembership,
)
from .tokens import generate_cancel_token, verify_cancel_token

logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Booking"],
    parameters=[
        OpenApiParameter(
            "active",
            OpenApiTypes.BOOL,
            description="Filter classes by active status (true/false)",
            required=False,
        )
    ],
    responses=FitnessClassSerializer(many=True),
)
class FitnessClassListView(generics.ListAPIView):
    """List all fitness classes. Optional `?active=true` to return only active ones."""

    serializer_class = FitnessClassSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = FitnessClass.objects.all().order_by("name")
        active_param = self.request.query_params.get("active")

        if active_param is not None:
            # ?active=true / ?active=false
            active = active_param.lower() in ("1", "true", "yes")
            qs = qs.filter(is_active=active)

        return qs


@extend_schema(tags=["Booking"], responses=FitnessClassSerializer(many=True))
class ActiveFitnessClassListView(generics.ListAPIView):
    """Returns all active fitness classes (GET /api/booking/fitness-classes/active)."""

    serializer_class = FitnessClassSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            FitnessClass.objects.filter(is_active=True)
            .prefetch_related("instructors")
            .order_by("name")
        )


@extend_schema(
    tags=["Booking"],
    parameters=[
        OpenApiParameter(
            "from_date",
            OpenApiTypes.DATE,
            description="Start date (YYYY-MM-DD). Defaults to today if omitted.",
            required=False,
        ),
        OpenApiParameter(
            "to_date",
            OpenApiTypes.DATE,
            description="End date (YYYY-MM-DD).",
            required=False,
        ),
        OpenApiParameter(
            "genre",
            OpenApiTypes.STR,
            description="Filter by fitness class genre.",
            required=False,
        ),
    ],
    responses=ClassSessionSerializer(many=True),
)
class UpcomingClassSessionListView(generics.ListAPIView):
    """List upcoming class sessions with optional date and genre filters."""

    serializer_class = ClassSessionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = ClassSession.objects.select_related("fitness_class").filter(
            status="scheduled"
        )

        # Date filtering
        from_date_str = self.request.query_params.get("from_date")
        to_date_str = self.request.query_params.get("to_date")

        if from_date_str:
            qs = qs.filter(date__gte=from_date_str)
        else:
            qs = qs.filter(date__gte=datetime.date.today())

        if to_date_str:
            qs = qs.filter(date__lte=to_date_str)

        # Genre filter
        genre = self.request.query_params.get("genre")
        if genre:
            qs = qs.filter(fitness_class__genre=genre)

        return qs.order_by("date", "start_time")


@extend_schema(
    tags=["Booking"],
    parameters=[
        OpenApiParameter(
            "pk",
            OpenApiTypes.UUID,
            description="Fitness class UUID",
            location=OpenApiParameter.PATH,
        )
    ],
    responses=ClassSessionSerializer(many=True),
)
class FitnessClassSessionsView(generics.ListAPIView):
    serializer_class = ClassSessionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        fitness_class_id = self.kwargs.get("pk")

        fitness_class = FitnessClass.objects.get(pk=fitness_class_id, is_active=True)
        today = datetime.date.today()

        qs = ClassSession.objects.filter(
            fitness_class=fitness_class,
            date__gte=today,
            status="scheduled",
        )

        days_param = self.request.query_params.get("days")
        if days_param:
            try:
                days = int(days_param)
                if days > 0:
                    end_date = today + datetime.timedelta(days=days)
                    qs = qs.filter(date__lte=end_date)
            except ValueError:
                pass

        qs = qs.order_by("date", "start_time")

        qs = qs.annotate(
            effective_capacity=Case(
                When(
                    capacity_override__isnull=False,
                    then=F("capacity_override"),
                ),
                default=F("fitness_class__capacity"),
                output_field=IntegerField(),
            ),
            booked_count=Count(
                "bookings",
                filter=Q(bookings__status=Booking.STATUS_BOOKED),
            ),
        ).annotate(
            remaining_spots=ExpressionWrapper(
                F("effective_capacity") - F("booked_count"),
                output_field=IntegerField(),
            )
        )
        return qs


@extend_schema(
    tags=["Booking"],
    parameters=[
        OpenApiParameter(
            "from_date",
            OpenApiTypes.DATE,
            description="Start date (YYYY-MM-DD). Defaults to today if omitted.",
            required=False,
        ),
        OpenApiParameter(
            "to_date",
            OpenApiTypes.DATE,
            description="End date (YYYY-MM-DD).",
            required=False,
        ),
        OpenApiParameter(
            "genre",
            OpenApiTypes.STR,
            description="Filter by fitness class genre.",
            required=False,
        ),
    ],
    responses=ClassSessionSerializer(many=True),
)
class AllUpcomingSessionsView(generics.ListAPIView):
    """List all upcoming class sessions across every fitness class.

    Supports the same filters as the single-class sessions endpoint:
      - `from_date` (YYYY-MM-DD) optional, default = today
      - `to_date`   (YYYY-MM-DD) optional
      - `genre`     filter by FitnessClass.genre
    """

    serializer_class = ClassSessionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = ClassSession.objects.select_related("fitness_class").filter(
            status="scheduled"
        )

        # Date filtering
        from_date_str = self.request.query_params.get("from_date")
        to_date_str = self.request.query_params.get("to_date")

        if from_date_str:
            qs = qs.filter(date__gte=from_date_str)
        else:
            qs = qs.filter(date__gte=datetime.date.today())

        if to_date_str:
            qs = qs.filter(date__lte=to_date_str)

        # Genre filter
        genre = self.request.query_params.get("genre")
        if genre:
            qs = qs.filter(fitness_class__genre=genre)

        return qs.order_by("date", "start_time")


class BookSessionView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, session_id):
        user = request.user if request.user.is_authenticated else None
        guest_name = request.data.get("guest_name", "").strip()
        guest_email = request.data.get("guest_email", "").strip()
        guest_phone = request.data.get("guest_phone", "").strip()

        session = get_object_or_404(
            ClassSession,
            pk=session_id,
            status="scheduled",
        )

        # Disallow booking past sessions
        today = datetime.date.today()
        if session.date < today:
            return Response(
                {"detail": "You cannot book a past session."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Capacity check
        effective_capacity = session.capacity_effective
        current_booked = session.bookings.filter(status=Booking.STATUS_BOOKED).count()

        if current_booked >= effective_capacity:
            return Response(
                {"detail": "This class is full."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if user already has an active booking
        if user:
            existing = Booking.objects.filter(
                user=user,
                class_session=session,
                status=Booking.STATUS_BOOKED,
            ).first()

            if existing:
                return Response(
                    {"detail": "You already have a booking for this session."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            if not guest_email:
                return Response(
                    {"detail": "guest_email is required for guest bookings."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Membership / payment logic (simplified)
        if user:
            can_book, reason = membership.can_book_session(user, session)
            if can_book:
                payment_status = Booking.PAYMENT_INCLUDED
            else:
                payment_status = Booking.PAYMENT_PENDING
        else:
            payment_status = Booking.PAYMENT_PENDING

        stripe_client_secret = None

        booking = Booking.objects.create(
            user=user,
            guest_name=guest_name,
            guest_email=guest_email,
            guest_phone=guest_phone,
            is_guest_purchase=user is None,
            class_session=session,
            status=Booking.STATUS_BOOKED,
            payment_status=payment_status,
        )

        cancel_token = generate_cancel_token("booking", booking.id)
        if payment_status == Booking.PAYMENT_INCLUDED and user:
            membership.consume_credit(user, session, n=1, reference_id=booking.id)
            whatsapp.send_booking_confirmation(booking)
            send_booking_confirmation_email(booking, cancel_token=cancel_token)
        else:
            try:
                payment_intent = payments.create_payment_intent_for_booking(booking)
            except ImproperlyConfigured:
                logger.exception(
                    "Stripe is not configured; deleting booking %s", booking.id
                )
                booking.delete()
                return Response(
                    {"detail": "Online payments are currently unavailable."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            except ValueError as exc:
                logger.exception(
                    "Invalid payment configuration for booking %s: %s",
                    booking.id,
                    exc,
                )
                booking.delete()
                return Response(
                    {"detail": str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except stripe.error.StripeError as exc:
                logger.exception(
                    "Stripe error while creating PaymentIntent for booking %s: %s",
                    booking.id,
                    exc,
                )
                booking.delete()
                return Response(
                    {"detail": "Unable to start payment. Please try again."},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            booking.stripe_payment_intent_id = payment_intent.id
            booking.save(update_fields=["stripe_payment_intent_id", "updated_at"])
            stripe_client_secret = payment_intent.client_secret

        serializer = BookingSerializer(booking)
        data = serializer.data
        if stripe_client_secret:
            data["stripe_client_secret"] = stripe_client_secret
        data["cancel_token"] = cancel_token
        # Send email only when booking is confirmed (paid or included)
        if payment_status == Booking.PAYMENT_INCLUDED:
            send_booking_confirmation_email(booking, cancel_token=cancel_token)

        return Response(data, status=status.HTTP_201_CREATED)


class CancelBookingView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, booking_id):
        user = request.user if request.user.is_authenticated else None

        booking = Booking.objects.filter(pk=booking_id).first()
        if booking is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        # Authenticated path: must own booking
        if user:
            if booking.user_id != user.id:
                return Response(
                    {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Guest path: require cancel token
            token = request.data.get("token") or request.query_params.get("token") or ""
            if not token or not verify_cancel_token(token, "booking", booking_id):
                return Response(
                    {"detail": "Invalid or missing cancel token."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if booking.user_id is not None:
                return Response(
                    {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
                )

        if booking.status != Booking.STATUS_BOOKED:
            return Response(
                {"detail": "This booking is not active."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session = booking.class_session
        # Cancellation cutoff (in hours) from settings or default 2h
        cutoff_hours = getattr(settings, "BOOKING_CANCELLATION_CUTOFF_HOURS", 2)

        # Build session start as naive datetime
        session_naive = datetime.datetime.combine(session.date, session.start_time)

        now = timezone.now()

        if timezone.is_aware(now):
            # Make session_dt aware in the same timezone as 'now'
            session_dt = timezone.make_aware(
                session_naive,
                timezone=timezone.get_current_timezone(),
            )
        else:
            # Both will be naive
            session_dt = session_naive

        if session_dt - now < datetime.timedelta(hours=cutoff_hours):
            return Response(
                {
                    "detail": (
                        "Cancellation window has passed. "
                        "Please contact the gym if you need help."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mark booking cancelled
        booking.status = Booking.STATUS_CANCELLED
        payment_status_changed = False
        if booking.payment_status == Booking.PAYMENT_PENDING:
            booking.payment_status = Booking.PAYMENT_VOID
            payment_status_changed = True

        update_fields = ["status", "updated_at"]
        if payment_status_changed:
            update_fields.append("payment_status")

        booking.save(update_fields=update_fields)

        # Restore credit if it was included in membership
        if booking.payment_status == Booking.PAYMENT_INCLUDED and booking.user:
            membership.restore_credit(user, session, n=1, reference_id=booking.id)

        whatsapp.send_booking_cancellation(booking)

        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MyBookingsListView(generics.ListAPIView):
    serializer_class = MyBookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = (
            Booking.objects.filter(user=user)
            .select_related("class_session", "class_session__fitness_class")
            .order_by("-class_session__date", "-class_session__start_time")
        )

        # Optional: filter upcoming only
        only_upcoming = self.request.query_params.get("upcoming")
        if only_upcoming and only_upcoming.lower() in ("1", "true", "yes"):
            today = datetime.date.today()
            qs = qs.filter(class_session__date__gte=today)

        return qs


@extend_schema(
    tags=["Stripe"], auth=[], request=None, responses={200: OpenApiTypes.OBJECT}
)
class StripeWebhookView(APIView):
    """
    Receives asynchronous events from Stripe to update booking payment states.
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
        logger.debug(
            "Stripe webhook (booking) event=%s intent=%s metadata_type=%s",
            event_type,
            data.get("id"),
            data.get("metadata", {}).get("type"),
        )
        if data.get("metadata", {}).get("type") not in (None, "booking"):
            logger.debug(
                "Ignoring Stripe event %s for booking webhook; metadata type=%s",
                event_type,
                data.get("metadata", {}).get("type"),
            )
            return Response({"received": True}, status=status.HTTP_200_OK)

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

        booking = Booking.objects.filter(stripe_payment_intent_id=intent_id).first()

        if not booking:
            # Membership purchase path
            purchase = MembershipPurchase.objects.filter(
                stripe_payment_intent_id=intent_id
            ).first()
            if purchase:
                if purchase.status != MembershipPurchase.STATUS_PAID:
                    purchase.status = MembershipPurchase.STATUS_PAID
                    purchase.save(update_fields=["status", "updated_at"])
                    UserMembership.objects.create(
                        user=purchase.user,
                        plan=purchase.plan,
                        remaining_class_sessions=purchase.plan.included_class_sessions,
                        remaining_events=purchase.plan.included_events,
                        status=UserMembership.STATUS_ACTIVE,
                    )
                    logger.info(
                        "Marked membership purchase %s as paid and granted membership.",
                        purchase.id,
                    )
                return

            logger.warning(
                "Stripe PaymentIntent %s was successful but no booking matched.",
                intent_id,
            )
            return

        if booking.payment_status == Booking.PAYMENT_PAID:
            return

        booking.payment_status = Booking.PAYMENT_PAID
        booking.save(update_fields=["payment_status", "updated_at"])
        whatsapp.send_booking_confirmation(booking)
        # Email confirmation (use cancel token)
        email_sent = send_booking_confirmation_email(
            booking, cancel_token=generate_cancel_token("booking", booking.id)
        )
        logger.info(
            "Marked booking %s as paid from Stripe webhook; email_sent=%s",
            booking.id,
            email_sent,
        )

    def _handle_payment_intent_failed(self, payload: dict) -> None:
        intent_id = payload.get("id")
        if not intent_id:
            logger.warning("Stripe event missing PaymentIntent id for failure handler.")
            return

        booking = Booking.objects.filter(stripe_payment_intent_id=intent_id).first()

        if not booking:
            purchase = MembershipPurchase.objects.filter(
                stripe_payment_intent_id=intent_id
            ).first()
            if purchase:
                if purchase.status != MembershipPurchase.STATUS_CANCELLED:
                    purchase.status = MembershipPurchase.STATUS_CANCELLED
                    purchase.save(update_fields=["status", "updated_at"])
                logger.warning(
                    "Membership purchase %s cancelled/failed for PaymentIntent %s",
                    purchase.id,
                    intent_id,
                )
                return

            logger.warning(
                "Stripe PaymentIntent %s failed but no booking matched.",
                intent_id,
            )
            return

        changed_fields = []
        if booking.status != Booking.STATUS_CANCELLED:
            booking.status = Booking.STATUS_CANCELLED
            changed_fields.append("status")
        if booking.payment_status != Booking.PAYMENT_VOID:
            booking.payment_status = Booking.PAYMENT_VOID
            changed_fields.append("payment_status")

        if changed_fields:
            changed_fields.append("updated_at")
            booking.save(update_fields=changed_fields)
            whatsapp.send_booking_cancellation(booking)
            logger.info(
                "Marked booking %s as cancelled/void due to failed Stripe payment.",
                booking.id,
            )


@extend_schema(
    tags=["Booking"],
    responses=FitnessClassSerializer,
)
class FitnessClassDetailView(RetrieveAPIView):
    """
    GET /api/booking/fitness-classes/<uuid:pk>/

    Return a single fitness class by ID.
    """

    queryset = FitnessClass.objects.all()
    serializer_class = FitnessClassSerializer
    permission_classes = [AllowAny]


class FitnessClassWithUpcomingSessionsView(RetrieveAPIView):
    """
    GET /booking/fitness-classes/<uuid:pk>/with-sessions/?days=30

    Returns a fitness class and its upcoming sessions
    in the next `days` days (default 30).
    """

    queryset = FitnessClass.objects.all()
    serializer_class = FitnessClassWithUpcomingSessionsSerializer
    permission_classes = [AllowAny]  # or IsAuthenticated

    def get_serializer_context(self):
        context = super().get_serializer_context()

        # read `days` from query params (?days=7)
        days_param = self.request.query_params.get("days")
        # we keep it as-is here; parsing/validation happens in the serializer
        if days_param is not None:
            context["days"] = days_param

        return context


class MembershipPlanListView(generics.ListAPIView):
    serializer_class = MembershipPlanSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return MembershipPlan.objects.filter(is_active=True).order_by("price", "name")


class MyMembershipView(generics.RetrieveAPIView):
    serializer_class = UserMembershipSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user = self.request.user
        return (
            UserMembership.objects.filter(
                user=user, status=UserMembership.STATUS_ACTIVE
            )
            .order_by("-starts_at")
            .first()
        )

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj:
            return Response(
                {"detail": "No active membership."}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(obj)
        return Response(serializer.data)


class MembershipChangeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Memberships"],
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        plan_id = request.data.get("plan_id")
        if not plan_id:
            return Response(
                {"detail": "plan_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        plan = MembershipPlan.objects.filter(id=plan_id, is_active=True).first()
        if not plan:
            return Response(
                {"detail": "Plan not found or inactive."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user
        # Cancel current active membership if exists
        current = (
            UserMembership.objects.filter(
                user=user, status=UserMembership.STATUS_ACTIVE
            )
            .order_by("-starts_at")
            .first()
        )
        if current:
            current.status = UserMembership.STATUS_CANCELLED
            current.save(update_fields=["status", "updated_at"])

        # If plan is free, grant immediately
        if plan.price == 0:
            membership_obj = UserMembership.objects.create(
                user=user,
                plan=plan,
                remaining_class_sessions=plan.included_class_sessions,
                remaining_events=plan.included_events,
                status=UserMembership.STATUS_ACTIVE,
            )
            serializer = UserMembershipSerializer(membership_obj)
            return Response(
                {
                    "membership": serializer.data,
                    "stripe_client_secret": None,
                    "purchase_id": None,
                },
                status=status.HTTP_201_CREATED,
            )

        # Paid plan: create a purchase + PaymentIntent
        purchase = MembershipPurchase.objects.create(
            user=user,
            plan=plan,
            amount=plan.price,
            status=MembershipPurchase.STATUS_PENDING,
        )

        try:
            intent = payments.create_payment_intent_for_membership(purchase)
        except ImproperlyConfigured:
            logger.exception(
                "Stripe not configured for membership plan change %s", purchase.id
            )
            purchase.delete()
            return Response(
                {"detail": "Online payments are currently unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except ValueError as exc:
            logger.exception(
                "Invalid payment configuration for membership purchase %s: %s",
                purchase.id,
                exc,
            )
            purchase.delete()
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except stripe.error.StripeError as exc:
            logger.exception(
                "Stripe error while creating PaymentIntent for membership purchase %s: %s",
                purchase.id,
                exc,
            )
            purchase.delete()
            return Response(
                {"detail": "Unable to start payment. Please try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        purchase.stripe_payment_intent_id = intent.id
        purchase.save(update_fields=["stripe_payment_intent_id", "updated_at"])

        return Response(
            {
                "purchase_id": purchase.id,
                "stripe_payment_intent_id": intent.id,
                "stripe_client_secret": intent.client_secret,
            },
            status=status.HTTP_201_CREATED,
        )


class MembershipCancelView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Memberships"],
        request=None,
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        user = request.user
        current = (
            UserMembership.objects.filter(
                user=user, status=UserMembership.STATUS_ACTIVE
            )
            .order_by("-starts_at")
            .first()
        )
        if not current:
            return Response(
                {"detail": "No active membership."}, status=status.HTTP_404_NOT_FOUND
            )

        current.status = UserMembership.STATUS_CANCELLED
        current.save(update_fields=["status", "updated_at"])
        return Response({"detail": "Membership cancelled."}, status=status.HTTP_200_OK)


class MembershipPurchaseView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Memberships"],
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        plan_id = request.data.get("plan_id")
        if not plan_id:
            return Response(
                {"detail": "plan_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        plan = MembershipPlan.objects.filter(id=plan_id, is_active=True).first()
        if not plan:
            return Response(
                {"detail": "Plan not found or inactive."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user

        # Free/zero-priced plan: grant immediately
        if plan.price == 0:
            membership_obj = UserMembership.objects.create(
                user=user,
                plan=plan,
                remaining_class_sessions=plan.included_class_sessions,
                remaining_events=plan.included_events,
                status=UserMembership.STATUS_ACTIVE,
            )
            serializer = UserMembershipSerializer(membership_obj)
            return Response(
                {"membership": serializer.data, "stripe_client_secret": None},
                status=status.HTTP_201_CREATED,
            )

        # Paid plan: create purchase + PaymentIntent
        purchase = MembershipPurchase.objects.create(
            user=user,
            plan=plan,
            amount=plan.price,
            status=MembershipPurchase.STATUS_PENDING,
        )

        try:
            intent = payments.create_payment_intent_for_membership(purchase)
        except ImproperlyConfigured:
            logger.exception(
                "Stripe is not configured for membership purchase %s", purchase.id
            )
            purchase.delete()
            return Response(
                {"detail": "Online payments are currently unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except ValueError as exc:
            logger.exception(
                "Invalid payment configuration for membership purchase %s: %s",
                purchase.id,
                exc,
            )
            purchase.delete()
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except stripe.error.StripeError as exc:
            logger.exception(
                "Stripe error while creating PaymentIntent for membership purchase %s: %s",
                purchase.id,
                exc,
            )
            purchase.delete()
            return Response(
                {"detail": "Unable to start payment. Please try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        purchase.stripe_payment_intent_id = intent.id
        purchase.save(update_fields=["stripe_payment_intent_id", "updated_at"])

        return Response(
            {
                "purchase_id": purchase.id,
                "stripe_payment_intent_id": intent.id,
                "stripe_client_secret": intent.client_secret,
            },
            status=status.HTTP_201_CREATED,
        )


class MembershipPlanListView(generics.ListAPIView):
    serializer_class = MembershipPlanSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return MembershipPlan.objects.filter(is_active=True).order_by("price", "name")


class MyMembershipView(generics.RetrieveAPIView):
    serializer_class = UserMembershipSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user = self.request.user
        return (
            UserMembership.objects.filter(
                user=user, status=UserMembership.STATUS_ACTIVE
            )
            .order_by("-starts_at")
            .first()
        )

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj:
            return Response(
                {"detail": "No active membership."}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(obj)
        return Response(serializer.data)
