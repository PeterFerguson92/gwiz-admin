# booking/views.py

import datetime  # add this

from django.conf import settings
from django.db.models import Case, Count, ExpressionWrapper, F, IntegerField, Q, When
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from booking.serializer import (
    BookingSerializer,
    ClassSessionSerializer,
    FitnessClassSerializer,
)

from . import membership
from .models import Booking, ClassSession, FitnessClass


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
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        user = request.user

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

        # Membership / payment logic (simplified)
        can_book, reason = membership.can_book_session(user, session)

        if can_book:
            payment_status = Booking.PAYMENT_INCLUDED
        else:
            # For now: create a pending booking; Stripe flow will complete payment
            payment_status = Booking.PAYMENT_PENDING

        booking = Booking.objects.create(
            user=user,
            class_session=session,
            status=Booking.STATUS_BOOKED,
            payment_status=payment_status,
        )

        if payment_status == Booking.PAYMENT_INCLUDED:
            membership.consume_credit(user, session, n=1)
            # later: trigger WhatsApp confirmation here

        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CancelBookingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        user = request.user

        # 1) Look up by PK only, then check ownership explicitly
        booking = Booking.objects.filter(pk=booking_id).first()
        if booking is None or booking.user_id != user.id:
            # Hide whether the booking exists if it's not theirs
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if booking.status != Booking.STATUS_BOOKED:
            return Response(
                {"detail": "This booking is not active."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session = booking.class_session

        # 2) Cancellation cutoff (in hours) from settings or default 2h
        cutoff_hours = getattr(settings, "BOOKING_CANCELLATION_CUTOFF_HOURS", 2)

        session_naive = datetime.datetime.combine(session.date, session.start_time)
        now = timezone.now()

        # Make both datetimes either aware or naive consistently
        if timezone.is_aware(now):
            session_dt = timezone.make_aware(
                session_naive,
                timezone=timezone.get_current_timezone(),
            )
        else:
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

        # 3) Mark booking cancelled
        booking.status = Booking.STATUS_CANCELLED
        booking.save(update_fields=["status", "updated_at"])

        # 4) Restore credit if it was included in membership
        if booking.payment_status == Booking.PAYMENT_INCLUDED:
            membership.restore_credit(user, session, n=1)

        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)

    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        user = request.user

        # Fetch by PK only, then check ownership explicitly.
        booking = Booking.objects.filter(pk=booking_id).first()
        if booking is None or booking.user_id != user.id:
            # Hide whether the booking exists if it's not theirs
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if booking.status != Booking.STATUS_BOOKED:
            return Response(
                {"detail": "This booking is not active."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session = booking.class_session

        # Cancellation cutoff (in hours) from settings or default 2h
        cutoff_hours = getattr(settings, "BOOKING_CANCELLATION_CUTOFF_HOURS", 2)

        # Build session start and 'now' in a consistent way
        session_naive = datetime.datetime.combine(session.date, session.start_time)
        now = timezone.now()

        if timezone.is_aware(now):
            session_dt = timezone.make_aware(
                session_naive,
                timezone=timezone.get_current_timezone(),
            )
        else:
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
        booking.save(update_fields=["status", "updated_at"])

        # Restore credit if it was included in membership
        if booking.payment_status == Booking.PAYMENT_INCLUDED:
            membership.restore_credit(user, session, n=1)

        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)

    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        user = request.user

        booking = get_object_or_404(
            Booking,
            pk=booking_id,
            user=user,
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
        booking.save(update_fields=["status", "updated_at"])

        # Restore credit if it was included in membership
        if booking.payment_status == Booking.PAYMENT_INCLUDED:
            membership.restore_credit(user, session, n=1)

        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MyBookingsListView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = (
            Booking.objects.filter(user=user)
            .select_related("class_session", "class_session.fitness_class")
            .order_by("-class_session__date", "-class_session__start_time")
        )

        # Optional: filter upcoming only
        only_upcoming = self.request.query_params.get("upcoming")
        if only_upcoming and only_upcoming.lower() in ("1", "true", "yes"):
            today = datetime.date.today()
        qs = (
            Booking.objects.filter(user=user)
            .select_related("class_session", "class_session__fitness_class")
            .order_by("-class_session__date", "-class_session__start_time")
        )

        return qs
