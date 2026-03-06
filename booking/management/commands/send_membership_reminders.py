import datetime
import logging
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from booking.email_utils import send_membership_renewal_email
from booking.models import MembershipReminderLog, UserMembership
from notifications.whatsapp import send_membership_renewal_reminder

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Send membership renewal reminders (7d, 3d, 1d) and expired notices. "
        "Safe to run daily with Heroku Scheduler."
    )

    REMINDER_BY_DAY = {
        7: MembershipReminderLog.TYPE_RENEW_7_DAYS,
        3: MembershipReminderLog.TYPE_RENEW_3_DAYS,
        1: MembershipReminderLog.TYPE_RENEW_1_DAY,
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be sent without writing reminder logs.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        now = timezone.now()
        today = now.date()
        base_renew_url = self._renew_url()

        qs = (
            UserMembership.objects.select_related("user", "plan")
            .filter(status=UserMembership.STATUS_ACTIVE)
            .exclude(next_reset_at__isnull=True)
            .order_by("next_reset_at")
        )

        processed = 0
        sent = 0
        skipped_existing = 0

        for membership in qs.iterator():
            reminder_type = self._determine_type(now, today, membership.next_reset_at)
            if reminder_type is None:
                continue

            processed += 1
            if MembershipReminderLog.objects.filter(
                membership=membership,
                reminder_type=reminder_type,
                cycle_reset_at=membership.next_reset_at,
            ).exists():
                skipped_existing += 1
                continue

            if dry_run:
                self.stdout.write(
                    f"[dry-run] membership={membership.id} user={membership.user_id} type={reminder_type}"
                )
                sent += 1
                continue

            with transaction.atomic():
                # If cycle boundary has passed, hard-expire membership.
                if (
                    reminder_type == MembershipReminderLog.TYPE_EXPIRED
                    and membership.status == UserMembership.STATUS_ACTIVE
                ):
                    membership.status = UserMembership.STATUS_EXPIRED
                    membership.expires_at = membership.next_reset_at
                    membership.save(
                        update_fields=["status", "expires_at", "updated_at"]
                    )

                renew_url = self._renew_url_for_membership(base_renew_url, membership)
                email_sent = send_membership_renewal_email(
                    membership,
                    reminder_type=reminder_type,
                    renew_url=renew_url,
                )
                whatsapp_sent = send_membership_renewal_reminder(
                    membership,
                    reminder_type=reminder_type,
                    renew_url=renew_url,
                )

                MembershipReminderLog.objects.create(
                    membership=membership,
                    reminder_type=reminder_type,
                    cycle_reset_at=membership.next_reset_at,
                    email_sent=email_sent,
                    whatsapp_sent=whatsapp_sent,
                )

            sent += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Processed={processed} sent={sent} skipped_existing={skipped_existing} dry_run={dry_run}"
            )
        )

    def _determine_type(
        self,
        now: datetime.datetime,
        today: datetime.date,
        reset_at: datetime.datetime,
    ):
        if now >= reset_at:
            return MembershipReminderLog.TYPE_EXPIRED
        reset_date = reset_at.date()
        days_until = (reset_date - today).days
        if days_until in self.REMINDER_BY_DAY:
            return self.REMINDER_BY_DAY[days_until]
        return None

    def _renew_url(self) -> str:
        explicit = getattr(settings, "MEMBERSHIP_RENEW_URL", "").strip()
        if explicit:
            if not urlparse(explicit).scheme:
                logger.warning(
                    "MEMBERSHIP_RENEW_URL is not absolute (%s). Reminder links may break.",
                    explicit,
                )
            return explicit

        base = getattr(settings, "PUBLIC_SITE_URL", "").strip() or "/"
        # Default fallback; can be overridden via MEMBERSHIP_RENEW_URL.
        renew_url = urljoin(base if base.endswith("/") else f"{base}/", "membership")
        if not urlparse(renew_url).scheme:
            logger.warning(
                "Derived membership renew URL is not absolute (%s). "
                "Set MEMBERSHIP_RENEW_URL to a full https URL.",
                renew_url,
            )
        return renew_url

    def _renew_url_for_membership(self, base_renew_url: str, membership) -> str:
        parsed = urlparse(base_renew_url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query["plan_id"] = str(membership.plan_id)
        return urlunparse(parsed._replace(query=urlencode(query)))
