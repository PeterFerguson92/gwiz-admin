# booking/serializers.py

from rest_framework import serializers

from .models import Booking, ClassSession, FitnessClass


class FitnessClassSerializer(serializers.ModelSerializer):
    instructors = serializers.StringRelatedField(many=True)

    class Meta:
        model = FitnessClass
        fields = [
            "id",
            "cover_image",
            "name",
            "description",
            "genre",
            "base_price",
            "default_duration_minutes",
            "capacity",
            "instructors",
            "additional_notes",
            "is_active",
        ]


class ClassSessionSerializer(serializers.ModelSerializer):
    fitness_class_id = serializers.UUIDField(source="fitness_class.pk", read_only=True)
    fitness_class_name = serializers.CharField(
        source="fitness_class.name", read_only=True
    )

    class Meta:
        model = ClassSession
        fields = [
            "id",
            "fitness_class_id",
            "fitness_class_name",
            "date",
            "start_time",
            "end_time",
            "status",
            "capacity_override",
            "price_override",
        ]


class BookingSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(
        source="class_session.fitness_class.name", read_only=True
    )
    class_date = serializers.DateField(source="class_session.date", read_only=True)
    class_start_time = serializers.TimeField(
        source="class_session.start_time", read_only=True
    )
    class_end_time = serializers.TimeField(
        source="class_session.end_time", read_only=True
    )

    class Meta:
        model = Booking
        fields = [
            "id",
            "user",
            "class_session",
            "class_name",
            "class_date",
            "class_start_time",
            "class_end_time",
            "status",
            "payment_status",
            "stripe_payment_intent_id",
            "attendance_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "status",
            "payment_status",
            "stripe_payment_intent_id",
            "attendance_status",
            "created_at",
            "updated_at",
        ]
