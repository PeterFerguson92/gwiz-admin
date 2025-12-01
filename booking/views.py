# booking/views.py

from datetime import date

from rest_framework import generics
from rest_framework.permissions import AllowAny  # or IsAuthenticated if you prefer

from booking.serializer import ClassSessionSerializer, FitnessClassSerializer

from .models import ClassSession, FitnessClass


class ActiveFitnessClassListView(generics.ListAPIView):
    """
    Returns all active fitness classes.

    GET /api/booking/fitness-classes/active
    """

    serializer_class = FitnessClassSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            FitnessClass.objects.filter(is_active=True)
            .prefetch_related("instructors")
            .order_by("name")
        )


class UpcomingClassSessionListView(generics.ListAPIView):
    """
    Simple read-only endpoint to list upcoming class sessions.

    Query params:
      - from_date (YYYY-MM-DD) optional, default = today
      - to_date   (YYYY-MM-DD) optional
      - genre     filter by FitnessClass.genre
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
            qs = qs.filter(date__gte=date.today())

        if to_date_str:
            qs = qs.filter(date__lte=to_date_str)

        # Genre filter
        genre = self.request.query_params.get("genre")
        if genre:
            qs = qs.filter(fitness_class__genre=genre)

        return qs.order_by("date", "start_time")
