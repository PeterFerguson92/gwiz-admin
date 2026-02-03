import datetime
import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from booking import payments
from booking.models import Booking

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Expire pending class bookings older than N minutes (default: 30)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--minutes",
            type=int,
            default=30,
            help="Age in minutes after which pending bookings are expired.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many bookings would be expired without updating.",
        )

    def handle(self, *args, **options):
        minutes = options["minutes"]
        dry_run = options["dry_run"]

        if minutes <= 0:
            self.stdout.write(self.style.ERROR("Minutes must be a positive integer."))
            return

        cutoff = timezone.now() - datetime.timedelta(minutes=minutes)
        qs = Booking.objects.filter(
            status=Booking.STATUS_BOOKED,
            payment_status=Booking.PAYMENT_PENDING,
            created_at__lte=cutoff,
        )
        total = qs.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[dry-run] Would expire {total} pending bookings older than {minutes} minutes."
                )
            )
            return

        expired = 0
        with transaction.atomic():
            for booking in qs.select_for_update():
                if booking.stripe_payment_intent_id and payments.stripe_enabled():
                    payments.cancel_payment_intent(booking.stripe_payment_intent_id)

                booking.status = Booking.STATUS_CANCELLED
                booking.payment_status = Booking.PAYMENT_VOID
                booking.save(update_fields=["status", "payment_status", "updated_at"])
                expired += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Expired {expired} pending bookings older than {minutes} minutes."
            )
        )
