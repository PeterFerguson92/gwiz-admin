# booking/views.py

import datetime  # add this

from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny

from booking.serializer import ClassSessionSerializer, FitnessClassSerializer

from .models import ClassSession, FitnessClass


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
            qs = qs.filter(date__gte=date.today())

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

        try:
            fitness_class = FitnessClass.objects.get(
                pk=fitness_class_id, is_active=True
            )
        except FitnessClass.DoesNotExist:
            raise NotFound("Fitness class not found or inactive.")

        # Use naive date instead of timezone.localdate()
        today = datetime.date.today()

        return ClassSession.objects.filter(
            fitness_class=fitness_class,
            date__gte=today,
            status="scheduled",
        ).order_by("date", "start_time")
