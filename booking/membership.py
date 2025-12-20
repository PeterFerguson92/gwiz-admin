def get_current_membership(user):
    # TODO: implement real lookup
    return None


def can_book_session(user, class_session):
    """
    Decide whether the user can book this session using membership credits.
    Return (can_book: bool, reason: str | None)
    """
    # TODO: implement real logic
    return False, "No active membership"


def consume_credit(user, class_session, n=1):
    """
    Deduct credits for a booking.
    """
    # TODO: implement real logic
    pass


def restore_credit(user, class_session, n=1):
    """
    Restore credits for a cancelled booking.
    """
    # TODO: implement real logic
    pass
