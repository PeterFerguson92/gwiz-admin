from rest_framework import serializers

from attendance.display import get_attendance_display_name
from booking.models import Booking
from events.models import EventTicket


class TicketAttendanceSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = EventTicket
        fields = [
            "id",
            "user_email",
            "status",
            "payment_status",
            "checked_in_at",
        ]

    def get_user_email(self, obj):
        if obj.user_id:
            return getattr(obj.user, "email", "")
        return obj.guest_email


class BookingAttendanceSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id",
            "user_email",
            "status",
            "payment_status",
            "checked_in_at",
        ]

    def get_user_email(self, obj):
        if obj.user_id:
            return getattr(obj.user, "email", "")
        return obj.guest_email


class CheckInByTokenSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    source = serializers.CharField(required=False, allow_blank=True, default="manual")
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class CheckInByTokenResponseSerializer(serializers.Serializer):
    kind = serializers.CharField()
    id = serializers.UUIDField()
    display_name = serializers.CharField()
    checked_in_at = serializers.DateTimeField()
