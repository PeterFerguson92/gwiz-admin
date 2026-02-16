import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from booking import membership
from booking.models import ClassSession, FitnessClass, MembershipPlan, UserMembership


class MembershipMonthlyResetTests(TestCase):
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

    def test_can_book_session_resets_membership_when_cycle_is_due(self):
        now = timezone.now()
        membership_obj = UserMembership.objects.create(
            user=self.user,
            plan=self.plan,
            remaining_class_sessions=0,
            remaining_events=0,
            status=UserMembership.STATUS_ACTIVE,
            starts_at=now - datetime.timedelta(days=35),
            next_reset_at=now - datetime.timedelta(days=1),
        )

        can_book, _ = membership.can_book_session(self.user, self.class_session)
        membership_obj.refresh_from_db()

        self.assertTrue(can_book)
        self.assertEqual(membership_obj.remaining_class_sessions, 5)
        self.assertEqual(membership_obj.remaining_events, 2)
        self.assertGreater(membership_obj.next_reset_at, now)

    def test_consume_credit_uses_reset_balance_after_month_boundary(self):
        now = timezone.now()
        membership_obj = UserMembership.objects.create(
            user=self.user,
            plan=self.plan,
            remaining_class_sessions=0,
            remaining_events=0,
            status=UserMembership.STATUS_ACTIVE,
            starts_at=now - datetime.timedelta(days=35),
            next_reset_at=now - datetime.timedelta(days=1),
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
        self.assertGreater(membership_obj.next_reset_at, now)
