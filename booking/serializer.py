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
    fitness_class = FitnessClassSerializer(read_only=True)
    capacity_effective = serializers.IntegerField(read_only=True)
    price_effective = serializers.DecimalField(
        max_digits=8, decimal_places=2, read_only=True
    )

    class Meta:
        model = ClassSession
        fields = [
            "id",
            "fitness_class",
            "date",
            "start_time",
            "end_time",
            "status",
            "capacity_override",
            "price_override",
            "capacity_effective",
            "price_effective",
        ]
