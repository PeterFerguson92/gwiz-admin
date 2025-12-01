# booking/serializers.py

from rest_framework import serializers

from .models import ClassSession, FitnessClass


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
