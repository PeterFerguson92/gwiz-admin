import datetime
from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from homepage.models import Trainer

from .models import Booking, ClassSession, FitnessClass, RecurrenceRule


class TrainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trainer
        fields = ["id", "name", "role", "instagram_link", "profile_image"]


class FitnessClassSerializer(serializers.ModelSerializer):
    instructors = TrainerSerializer(many=True, read_only=True)

    class Meta:
        model = FitnessClass
        fields = [
            "id",
            "cover_image",
            "name",
            "description",
            "genre",
            "base_price",
            "payment_link",
            "default_duration_minutes",
            "capacity",
            "instructors",
            "additional_notes",
            "is_active",
            "created_at",
            "updated_at",
        ]


class RecurrenceRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurrenceRule
        fields = [
            "id",
            "fitness_class",
            "recurrence_type",
            "days_of_week",
            "start_time",
            "end_time",
            "start_date",
            "end_date",
            "rrule",
            "is_active",
            "created_at",
        ]


class ClassSessionSerializer(serializers.ModelSerializer):
    # expose computed properties
    capacity_effective = serializers.IntegerField(read_only=True)
    price_effective = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        read_only=True,
    )
    spaces_left = serializers.SerializerMethodField()

    # override created_at to handle naive datetimes safely
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = ClassSession
        fields = "__all__"

    def get_created_at(self, obj):
        """
        Return a timezone-aware ISO8601 string for created_at,
        fixing naive datetimes if any exist in the DB.
        """
        value = obj.created_at
        if value is None:
            return None

        if timezone.is_naive(value):
            value = timezone.make_aware(
                value,
                timezone.get_current_timezone(),
            )

        # let DRF/json render this as a string
        return value.isoformat()

    def get_spaces_left(self, obj):
        """
        Calculate remaining spaces: effective capacity minus booked count.
        """
        effective_capacity = obj.capacity_effective
        booked_count = obj.bookings.filter(status=Booking.STATUS_BOOKED).count()
        spaces_left = effective_capacity - booked_count
        return max(0, spaces_left)  # Ensure it doesn't go negative


class BookingSerializer(serializers.ModelSerializer):
    # helper flags
    is_active = serializers.BooleanField(read_only=True)
    is_included = serializers.BooleanField(read_only=True)
    is_paid = serializers.BooleanField(read_only=True)
    attendance_marked = serializers.BooleanField(read_only=True)
    is_present = serializers.BooleanField(read_only=True)
    is_no_show = serializers.BooleanField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "user",
            "class_session",
            "status",
            "payment_status",
            "stripe_payment_intent_id",
            "attendance_status",
            "created_at",
            "updated_at",
            "is_active",
            "is_included",
            "is_paid",
            "attendance_marked",
            "is_present",
            "is_no_show",
        ]


class FitnessClassSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = FitnessClass
        fields = ["id", "name", "genre"]


class ClassSessionSummarySerializer(serializers.ModelSerializer):
    fitness_class = FitnessClassSummarySerializer(read_only=True)

    class Meta:
        model = ClassSession
        fields = ["id", "date", "start_time", "end_time", "fitness_class"]


class MyBookingSerializer(serializers.ModelSerializer):
    class_session = ClassSessionSummarySerializer(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "status",
            "payment_status",
            "attendance_status",
            "created_at",
            "class_session",
        ]


class FitnessClassWithUpcomingSessionsSerializer(FitnessClassSerializer):
    upcoming_sessions = serializers.SerializerMethodField()

    class Meta(FitnessClassSerializer.Meta):
        fields = FitnessClassSerializer.Meta.fields + ["upcoming_sessions"]

    def get_upcoming_sessions(self, obj):
        """
        Return sessions for this class in the next `days` days
        (coming from serializer context), default 30.
        """
        days = self.context.get("days", 30)

        # robust parsing & bounds
        try:
            days = int(days)
        except (TypeError, ValueError):
            days = 30

        if days < 0:
            days = 0
        if days > 365:
            days = 365

        # 🔧 IMPORTANT CHANGE: don't use timezone.localdate()
        today = datetime.date.today()
        end_date = today + datetime.timedelta(days=days)

        qs = obj.sessions.filter(
            status="scheduled",
            date__gte=today,
            date__lte=end_date,
        ).order_by("date", "start_time")

        return ClassSessionSerializer(qs, many=True).data
