from django.db import transaction
from django.utils import timezone

from booking.models import MembershipUsage, UserMembership


def _reset_membership_if_due(membership, now):
    """
    Ensure cycle metadata is initialized and expire membership when due.
    """
    next_reset_at = membership.next_reset_at
    changed_fields = []

    if next_reset_at is None:
        base = membership.starts_at or now
        next_reset_at = UserMembership.initial_next_reset_at(base)
        membership.next_reset_at = next_reset_at
        changed_fields.append("next_reset_at")

    if membership.expires_at is None:
        membership.expires_at = next_reset_at
        changed_fields.append("expires_at")

    if now >= next_reset_at and membership.status == UserMembership.STATUS_ACTIVE:
        membership.status = UserMembership.STATUS_EXPIRED
        changed_fields.append("status")

    if changed_fields:
        membership.save(update_fields=[*changed_fields, "updated_at"])


def _get_active_membership(user):
    """
    Return the most recent active membership for the user (if any).
    """
    if user is None:
        return None
    now = timezone.now()
    qs = UserMembership.objects.select_for_update().filter(
        status=UserMembership.STATUS_ACTIVE, user=user
    )
    membership = qs.order_by("-starts_at").first()
    if not membership:
        return None

    _reset_membership_if_due(membership, now)
    if membership.status != UserMembership.STATUS_ACTIVE:
        return None
    return membership


def can_book_session(user, class_session, n=1):
    """
    Decide whether the user can book this session using membership credits.
    Return (can_book: bool, reason: str | None)
    """
    with transaction.atomic():
        membership = _get_active_membership(user)
        if not membership:
            return False, "No active membership"

        if membership.remaining_class_sessions < n:
            return False, "Not enough class sessions remaining"

        return True, None


def consume_credit(user, class_session, n=1, reference_id=None):
    """
    Deduct class session credits for a booking.
    """
    with transaction.atomic():
        membership = _get_active_membership(user)
        if not membership:
            return False
        if membership.remaining_class_sessions < n:
            return False
        membership.remaining_class_sessions -= n
        membership.save(update_fields=["remaining_class_sessions", "updated_at"])
        MembershipUsage.objects.create(
            membership=membership,
            kind=MembershipUsage.KIND_CLASS,
            amount=n,
            reference_id=reference_id,
        )
        return True


def restore_credit(user, class_session, n=1, reference_id=None):
    """
    Restore class session credits for a cancelled booking.
    """
    with transaction.atomic():
        membership = _get_active_membership(user)
        if not membership:
            return False
        membership.remaining_class_sessions += n
        membership.save(update_fields=["remaining_class_sessions", "updated_at"])
        MembershipUsage.objects.create(
            membership=membership,
            kind=MembershipUsage.KIND_CLASS,
            amount=n,
            reference_id=reference_id,
            reversed=True,
        )
        return True


# Event helpers
def can_book_event(user, event, n=1):
    with transaction.atomic():
        membership = _get_active_membership(user)
        if not membership:
            return False, "No active membership"
        if membership.remaining_events < n:
            return False, "Not enough event credits remaining"
        return True, None


def consume_event_credit(user, event, n=1, reference_id=None):
    with transaction.atomic():
        membership = _get_active_membership(user)
        if not membership:
            return False
        if membership.remaining_events < n:
            return False
        membership.remaining_events -= n
        membership.save(update_fields=["remaining_events", "updated_at"])
        MembershipUsage.objects.create(
            membership=membership,
            kind=MembershipUsage.KIND_EVENT,
            amount=n,
            reference_id=reference_id,
        )
        return True


def restore_event_credit(user, event, n=1, reference_id=None):
    with transaction.atomic():
        membership = _get_active_membership(user)
        if not membership:
            return False
        membership.remaining_events += n
        membership.save(update_fields=["remaining_events", "updated_at"])
        MembershipUsage.objects.create(
            membership=membership,
            kind=MembershipUsage.KIND_EVENT,
            amount=n,
            reference_id=reference_id,
            reversed=True,
        )
        return True
