from rest_framework import serializers

from .models import Event, EventTicket


class EventSerializer(serializers.ModelSerializer):
    remaining_tickets = serializers.IntegerField(read_only=True)
    is_sold_out = serializers.BooleanField(read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "cover_image",
            "name",
            "description",
            "location",
            "start_datetime",
            "end_datetime",
            "ticket_price",
            "payment_link",
            "capacity",
            "remaining_tickets",
            "is_sold_out",
            "is_featured",
        ]


class EventTicketSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)

    class Meta:
        model = EventTicket
        fields = [
            "id",
            "event",
            "user",
            "guest_name",
            "guest_email",
            "guest_phone",
            "quantity",
            "status",
            "payment_status",
            "payment_provider",
            "stripe_payment_intent_id",
            "truelayer_payment_id",
            "truelayer_payment_status",
            "truelayer_payment_reference",
            "created_at",
            "updated_at",
        ]
        read_only_fields = (
            "status",
            "payment_status",
            "payment_provider",
            "stripe_payment_intent_id",
            "truelayer_payment_id",
            "truelayer_payment_status",
            "truelayer_payment_reference",
            "created_at",
            "updated_at",
            "user",
        )


class PurchaseRequestSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, default=1)
