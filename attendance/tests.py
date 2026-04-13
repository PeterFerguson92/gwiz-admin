import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from attendance.models import AttendanceLog
from attendance.rules import can_check_in_booking, can_check_in_ticket
from attendance.services import (
    AlreadyCheckedIn,
    CheckInNotAllowed,
    NotCheckedIn,
    check_in_booking,
    check_in_ticket,
    revert_booking_check_in,
    revert_ticket_check_in,
)
from booking.models import Booking, ClassSession, FitnessClass
from events.models import Event, EventTicket


class AttendanceBaseTestCase(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.staff_user = user_model.objects.create_user(
            username="staff",
            email="staff@example.com",
            password="pass1234",
            is_staff=True,
        )
        self.member_user = user_model.objects.create_user(
            username="member",
            email="member@example.com",
            password="pass1234",
        )
        self.other_user = user_model.objects.create_user(
            username="other",
            email="other@example.com",
            password="pass1234",
        )
        self.api_client = APIClient()

        self.event = Event.objects.create(
            name="Mobility Workshop",
            description="Event description",
            location="Studio A",
            start_datetime=timezone.now() + datetime.timedelta(days=2),
            end_datetime=timezone.now() + datetime.timedelta(days=2, hours=2),
            ticket_price=Decimal("15.00"),
            capacity=50,
            is_active=True,
        )
        self.other_event = Event.objects.create(
            name="Breathwork Lab",
            description="Another event",
            location="Studio B",
            start_datetime=timezone.now() + datetime.timedelta(days=4),
            end_datetime=timezone.now() + datetime.timedelta(days=4, hours=1),
            ticket_price=Decimal("20.00"),
            capacity=30,
            is_active=True,
        )
        self.fitness_class = FitnessClass.objects.create(
            name="Yoga Flow",
            description="Class description",
            genre="yoga",
            base_price=Decimal("12.00"),
            capacity=20,
            is_active=True,
        )
        self.class_session = ClassSession.objects.create(
            fitness_class=self.fitness_class,
            date=datetime.date.today() + datetime.timedelta(days=2),
            start_time=datetime.time(10, 0),
            end_time=datetime.time(11, 0),
            status="scheduled",
        )
        self.other_fitness_class = FitnessClass.objects.create(
            name="Pilates Core",
            description="Other class description",
            genre="pilates",
            base_price=Decimal("14.00"),
            capacity=18,
            is_active=True,
        )
        self.other_class_session = ClassSession.objects.create(
            fitness_class=self.other_fitness_class,
            date=datetime.date.today() + datetime.timedelta(days=3),
            start_time=datetime.time(12, 0),
            end_time=datetime.time(13, 0),
            status="scheduled",
        )

    def create_ticket(
        self,
        *,
        user=None,
        guest_email="",
        status_value=EventTicket.STATUS_CONFIRMED,
        payment_status=EventTicket.PAYMENT_PAID,
        checked_in_at=None,
        event=None,
    ):
        return EventTicket.objects.create(
            event=event or self.event,
            user=user,
            is_guest_purchase=user is None,
            guest_email=guest_email,
            guest_name="Guest User" if user is None else "",
            status=status_value,
            payment_status=payment_status,
            quantity=1,
            checked_in_at=checked_in_at,
        )

    def create_booking(
        self,
        *,
        user=None,
        guest_email="",
        status_value=Booking.STATUS_BOOKED,
        payment_status=Booking.PAYMENT_PAID,
        checked_in_at=None,
        class_session=None,
    ):
        return Booking.objects.create(
            class_session=class_session or self.class_session,
            user=user,
            is_guest_purchase=user is None,
            guest_email=guest_email,
            guest_name="Guest Booker" if user is None else "",
            status=status_value,
            payment_status=payment_status,
            checked_in_at=checked_in_at,
        )

    def authenticate_staff(self):
        self.api_client.force_authenticate(user=self.staff_user)

    def authenticate_non_staff(self):
        self.api_client.force_authenticate(user=self.member_user)


class AttendanceRulesTests(AttendanceBaseTestCase):
    def test_ticket_rule_allows_confirmed_paid_ticket(self):
        ticket = self.create_ticket(user=self.member_user)

        allowed, reason = can_check_in_ticket(ticket)

        self.assertTrue(allowed)
        self.assertIsNone(reason)

    def test_ticket_rule_blocks_cancelled_pending_and_duplicate(self):
        cancelled_ticket = self.create_ticket(
            user=self.member_user,
            status_value=EventTicket.STATUS_CANCELLED,
            payment_status=EventTicket.PAYMENT_PAID,
        )
        pending_ticket = self.create_ticket(
            user=self.member_user,
            status_value=EventTicket.STATUS_CONFIRMED,
            payment_status=EventTicket.PAYMENT_PENDING,
        )
        duplicate_ticket = self.create_ticket(
            user=self.member_user,
            checked_in_at=timezone.now(),
        )

        self.assertEqual(
            can_check_in_ticket(cancelled_ticket), (False, "Ticket is cancelled.")
        )
        self.assertEqual(
            can_check_in_ticket(pending_ticket), (False, "Ticket payment is pending.")
        )
        self.assertEqual(
            can_check_in_ticket(duplicate_ticket),
            (False, "Ticket has already been checked in."),
        )

    def test_booking_rule_allows_staff_user_even_if_otherwise_blocked(self):
        booking = self.create_booking(
            user=self.staff_user,
            status_value=Booking.STATUS_CANCELLED,
            payment_status=Booking.PAYMENT_PENDING,
        )

        allowed, reason = can_check_in_booking(booking)

        self.assertTrue(allowed)
        self.assertIsNone(reason)

    def test_booking_rule_blocks_invalid_status_and_void_payment(self):
        booking = self.create_booking(
            user=self.member_user,
            status_value=Booking.STATUS_CANCELLED,
            payment_status=Booking.PAYMENT_VOID,
        )

        allowed, reason = can_check_in_booking(booking)

        self.assertFalse(allowed)
        self.assertEqual(reason, "Booking is cancelled.")


class AttendanceServicesTests(AttendanceBaseTestCase):
    def test_check_in_ticket_updates_fields_and_creates_log(self):
        ticket = self.create_ticket(user=self.member_user)

        check_in_ticket(
            ticket,
            actor=self.staff_user,
            source="manual",
            notes="Front desk",
        )

        ticket.refresh_from_db()
        log = AttendanceLog.objects.get(
            target_type=AttendanceLog.TARGET_TICKET,
            target_id=str(ticket.id),
        )
        self.assertIsNotNone(ticket.checked_in_at)
        self.assertEqual(ticket.checked_in_by, self.staff_user)
        self.assertEqual(log.action, AttendanceLog.ACTION_CHECKED_IN)
        self.assertEqual(log.actor, self.staff_user)
        self.assertEqual(log.notes, "Front desk")

    def test_check_in_booking_raises_not_allowed_for_pending_booking(self):
        booking = self.create_booking(
            user=self.member_user,
            payment_status=Booking.PAYMENT_PENDING,
        )

        with self.assertRaises(CheckInNotAllowed):
            check_in_booking(booking, actor=self.staff_user)

    def test_duplicate_ticket_check_in_raises_already_checked_in(self):
        ticket = self.create_ticket(
            user=self.member_user,
            checked_in_at=timezone.now(),
        )

        with self.assertRaises(AlreadyCheckedIn):
            check_in_ticket(ticket, actor=self.staff_user)

    def test_revert_booking_check_in_clears_fields_and_creates_log(self):
        booking = self.create_booking(user=self.member_user)
        check_in_booking(booking, actor=self.staff_user, notes="Initial")

        revert_booking_check_in(
            booking,
            actor=self.staff_user,
            source="manual",
            notes="Undo",
        )

        booking.refresh_from_db()
        logs = AttendanceLog.objects.filter(
            target_type=AttendanceLog.TARGET_BOOKING,
            target_id=str(booking.id),
        ).order_by("created_at")
        self.assertIsNone(booking.checked_in_at)
        self.assertIsNone(booking.checked_in_by)
        self.assertEqual(logs.count(), 2)
        self.assertEqual(logs.last().action, AttendanceLog.ACTION_REVERTED)
        self.assertEqual(logs.last().notes, "Undo")

    def test_revert_ticket_check_in_raises_when_not_checked_in(self):
        ticket = self.create_ticket(user=self.member_user)

        with self.assertRaises(NotCheckedIn):
            revert_ticket_check_in(ticket, actor=self.staff_user)


class AttendanceWriteEndpointTests(AttendanceBaseTestCase):
    def test_ticket_check_in_endpoint_requires_staff(self):
        ticket = self.create_ticket(user=self.member_user)
        self.authenticate_non_staff()

        response = self.api_client.post(
            f"/api/events/tickets/{ticket.id}/check-in/",
            {"source": "manual", "notes": "Desk"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_ticket_check_in_endpoint_and_revert_flow(self):
        ticket = self.create_ticket(user=self.member_user)
        self.authenticate_staff()

        check_in_response = self.api_client.post(
            f"/api/events/tickets/{ticket.id}/check-in/",
            {"source": "manual", "notes": "Desk"},
            format="json",
        )
        duplicate_response = self.api_client.post(
            f"/api/events/tickets/{ticket.id}/check-in/",
            {"source": "manual"},
            format="json",
        )
        revert_response = self.api_client.post(
            f"/api/events/tickets/{ticket.id}/revert-check-in/",
            {"notes": "Undo"},
            format="json",
        )

        ticket.refresh_from_db()
        self.assertEqual(check_in_response.status_code, status.HTTP_200_OK)
        self.assertEqual(check_in_response.data["id"], str(ticket.id))
        self.assertIsNotNone(check_in_response.data["checked_in_at"])
        self.assertEqual(duplicate_response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(revert_response.status_code, status.HTTP_200_OK)
        self.assertIsNone(revert_response.data["checked_in_at"])
        self.assertIsNone(ticket.checked_in_at)

    def test_ticket_check_in_endpoint_returns_403_for_blocked_ticket(self):
        ticket = self.create_ticket(
            user=self.member_user,
            payment_status=EventTicket.PAYMENT_PENDING,
        )
        self.authenticate_staff()

        response = self.api_client.post(
            f"/api/events/tickets/{ticket.id}/check-in/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"detail": "Ticket payment is pending."})

    def test_booking_revert_endpoint_returns_400_when_not_checked_in(self):
        booking = self.create_booking(user=self.member_user)
        self.authenticate_staff()

        response = self.api_client.post(
            f"/api/booking/bookings/{booking.id}/revert-check-in/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": "Booking is not checked in."})

    def test_booking_check_in_endpoint_creates_log(self):
        booking = self.create_booking(user=self.member_user)
        self.authenticate_staff()

        response = self.api_client.post(
            f"/api/booking/bookings/{booking.id}/check-in/",
            {"source": "manual", "notes": "Studio"},
            format="json",
        )

        booking.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(booking.checked_in_at)
        self.assertTrue(
            AttendanceLog.objects.filter(
                target_type=AttendanceLog.TARGET_BOOKING,
                target_id=str(booking.id),
                action=AttendanceLog.ACTION_CHECKED_IN,
            ).exists()
        )


class AttendanceReadEndpointTests(AttendanceBaseTestCase):
    def test_event_attendee_list_is_staff_only_and_paginated(self):
        ticket = self.create_ticket(user=self.member_user)
        self.authenticate_non_staff()

        forbidden = self.api_client.get(f"/api/events/{self.event.id}/attendees/")
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        self.authenticate_staff()
        response = self.api_client.get(
            f"/api/events/{self.event.id}/attendees/",
            {"page_size": 1},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], str(ticket.id))
        self.assertEqual(
            response.data["results"][0]["user_email"], self.member_user.email
        )

    def test_session_attendee_list_returns_guest_email(self):
        booking = self.create_booking(
            user=None, guest_email="guest-booking@example.com"
        )
        self.authenticate_staff()

        response = self.api_client.get(
            f"/api/booking/sessions/{self.class_session.id}/attendees/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["id"], str(booking.id))
        self.assertEqual(
            response.data["results"][0]["user_email"],
            "guest-booking@example.com",
        )

    def test_ticket_search_supports_member_email_guest_email_and_exact_uuid(self):
        member_ticket = self.create_ticket(user=self.member_user)
        guest_ticket = self.create_ticket(
            user=None, guest_email="guest-ticket@example.com"
        )
        self.authenticate_staff()

        member_response = self.api_client.get(
            "/api/events/tickets/search/",
            {"q": self.member_user.email},
        )
        guest_response = self.api_client.get(
            "/api/events/tickets/search/",
            {"q": "guest-ticket@example.com"},
        )
        uuid_response = self.api_client.get(
            "/api/events/tickets/search/",
            {"q": str(member_ticket.id)},
        )

        self.assertEqual(member_response.status_code, status.HTTP_200_OK)
        self.assertEqual(member_response.data["count"], 1)
        self.assertEqual(
            member_response.data["results"][0]["id"], str(member_ticket.id)
        )
        self.assertEqual(guest_response.data["count"], 1)
        self.assertEqual(guest_response.data["results"][0]["id"], str(guest_ticket.id))
        self.assertEqual(uuid_response.data["count"], 1)
        self.assertEqual(uuid_response.data["results"][0]["id"], str(member_ticket.id))

    def test_event_scoped_ticket_search_only_returns_tickets_for_current_event(self):
        matching_ticket = self.create_ticket(user=self.member_user)
        self.create_ticket(
            user=None,
            guest_email=self.member_user.email,
            event=self.other_event,
        )
        self.authenticate_staff()

        response = self.api_client.get(
            f"/api/events/{self.event.id}/tickets/search/",
            {"q": self.member_user.email},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(matching_ticket.id))

    def test_booking_search_supports_member_email_guest_email_and_exact_uuid(self):
        member_booking = self.create_booking(user=self.member_user)
        guest_booking = self.create_booking(
            user=None,
            guest_email="guest-attendee@example.com",
        )
        self.authenticate_staff()

        member_response = self.api_client.get(
            "/api/booking/bookings/search/",
            {"q": self.member_user.email},
        )
        guest_response = self.api_client.get(
            "/api/booking/bookings/search/",
            {"q": "guest-attendee@example.com"},
        )
        uuid_response = self.api_client.get(
            "/api/booking/bookings/search/",
            {"q": str(guest_booking.id)},
        )

        self.assertEqual(member_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            member_response.data["results"][0]["id"], str(member_booking.id)
        )
        self.assertEqual(guest_response.data["results"][0]["id"], str(guest_booking.id))
        self.assertEqual(uuid_response.data["count"], 1)
        self.assertEqual(uuid_response.data["results"][0]["id"], str(guest_booking.id))

    def test_session_scoped_booking_search_only_returns_bookings_for_current_session(
        self,
    ):
        matching_booking = self.create_booking(user=self.member_user)
        self.create_booking(
            user=None,
            guest_email=self.member_user.email,
            class_session=self.other_class_session,
        )
        self.authenticate_staff()

        response = self.api_client.get(
            f"/api/booking/sessions/{self.class_session.id}/bookings/search/",
            {"q": self.member_user.email},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(matching_booking.id))
