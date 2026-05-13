import datetime
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from booking import membership
from booking.models import (
    ClassSession,
    FitnessClass,
    MembershipPlan,
    MembershipReminderLog,
    RecurrenceRule,
    UserMembership,
)


class MembershipLifecycleTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="member",
            email="member@example.com",
            password="pass1234",
        )
        self.plan = MembershipPlan.objects.create(
            name="Monthly 5",
            description="Monthly plan",
            price=Decimal("99.00"),
            included_class_sessions=5,
            included_events=2,
        )
        self.fitness_class = FitnessClass.objects.create(
            name="Yoga",
            description="Yoga class",
            genre="yoga",
            base_price=Decimal("20.00"),
            capacity=20,
        )
        self.class_session = ClassSession.objects.create(
            fitness_class=self.fitness_class,
            date=timezone.localdate() + datetime.timedelta(days=3),
            start_time=datetime.time(10, 0),
            end_time=datetime.time(11, 0),
        )

    def test_can_book_session_expires_membership_when_cycle_is_due(self):
        now = timezone.now()
        membership_obj = UserMembership.objects.create(
            user=self.user,
            plan=self.plan,
            remaining_class_sessions=2,
            remaining_events=1,
            status=UserMembership.STATUS_ACTIVE,
            starts_at=now - datetime.timedelta(days=35),
            next_reset_at=now - datetime.timedelta(days=1),
            expires_at=now - datetime.timedelta(days=1),
        )

        can_book, _ = membership.can_book_session(self.user, self.class_session)
        membership_obj.refresh_from_db()

        self.assertFalse(can_book)
        self.assertEqual(membership_obj.status, UserMembership.STATUS_EXPIRED)
        self.assertEqual(membership_obj.remaining_class_sessions, 2)
        self.assertEqual(membership_obj.remaining_events, 1)

    def test_consume_credit_succeeds_when_membership_is_in_cycle(self):
        now = timezone.now()
        reset_at = now + datetime.timedelta(days=10)
        membership_obj = UserMembership.objects.create(
            user=self.user,
            plan=self.plan,
            remaining_class_sessions=5,
            remaining_events=2,
            status=UserMembership.STATUS_ACTIVE,
            starts_at=now - datetime.timedelta(days=20),
            next_reset_at=reset_at,
            expires_at=reset_at,
        )

        consumed = membership.consume_credit(
            self.user,
            self.class_session,
            reference_id=self.class_session.id,
        )
        membership_obj.refresh_from_db()

        self.assertTrue(consumed)
        self.assertEqual(membership_obj.remaining_class_sessions, 4)
        self.assertEqual(membership_obj.remaining_events, 2)

    def test_membership_reminder_log_is_unique_per_cycle(self):
        now = timezone.now()
        reset_at = now + datetime.timedelta(days=7)
        membership_obj = UserMembership.objects.create(
            user=self.user,
            plan=self.plan,
            remaining_class_sessions=5,
            remaining_events=2,
            status=UserMembership.STATUS_ACTIVE,
            next_reset_at=reset_at,
            expires_at=reset_at,
        )
        MembershipReminderLog.objects.create(
            membership=membership_obj,
            reminder_type=MembershipReminderLog.TYPE_RENEW_7_DAYS,
            cycle_reset_at=reset_at,
            email_sent=True,
            whatsapp_sent=False,
        )

        with self.assertRaises(IntegrityError):
            MembershipReminderLog.objects.create(
                membership=membership_obj,
                reminder_type=MembershipReminderLog.TYPE_RENEW_7_DAYS,
                cycle_reset_at=reset_at,
                email_sent=True,
                whatsapp_sent=True,
            )


class RecurrenceRuleAdminGenerationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="pass1234",
        )
        self.client.force_login(self.admin_user)
        self.fitness_class = FitnessClass.objects.create(
            name="Sunday Open Gym",
            description="Open gym session",
            genre="open_gym",
            base_price=Decimal("10.00"),
            capacity=25,
        )

    @mock.patch("booking.admin.date")
    def test_generate_sessions_uses_rule_end_date_when_present(self, mock_date):
        mock_date.today.return_value = datetime.date(2026, 5, 13)
        rule = RecurrenceRule.objects.create(
            fitness_class=self.fitness_class,
            recurrence_type="weekly",
            days_of_week=["sun"],
            start_time=datetime.time(10, 0),
            end_time=datetime.time(12, 0),
            start_date=datetime.date(2026, 5, 13),
            end_date=datetime.date(2026, 12, 31),
            is_active=True,
        )

        response = self.client.post(
            reverse("admin:booking_recurrencerule_generate_sessions", args=[rule.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            ClassSession.objects.filter(
                created_from_rule=rule,
                date=datetime.date(2026, 12, 27),
            ).exists()
        )
