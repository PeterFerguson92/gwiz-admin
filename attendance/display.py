def get_attendance_display_name(obj) -> str:
    user = getattr(obj, "user", None)
    if user:
        return (
            user.get_full_name() or getattr(user, "full_name", "") or user.email or "—"
        )

    guest_name = getattr(obj, "guest_name", "") or ""
    if guest_name:
        return f"Guest: {guest_name}"

    guest_email = getattr(obj, "guest_email", "") or ""
    if guest_email:
        return f"Guest: {guest_email}"

    return "Guest"
