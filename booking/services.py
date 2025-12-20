from datetime import timedelta

from booking.models import ClassSession, RecurrenceRule


def _matches_rule(current_date, rule: RecurrenceRule) -> bool:
    WEEKDAY_MAP = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

    if rule.recurrence_type == "one_off":
        return current_date == rule.start_date

    if rule.recurrence_type == "daily":
        return True

    weekday_code = WEEKDAY_MAP[current_date.weekday()]

    if rule.recurrence_type in ("weekly", "multi_weekly"):
        return weekday_code in (rule.days_of_week or [])

    return False


def generate_sessions_for_rule(rule, from_date, to_date):
    """
    Actually create sessions, returning (created, skipped_existing).
    """
    created = 0
    skipped = 0

    start = max(rule.start_date, from_date)
    end = min(rule.end_date or to_date, to_date)

    current = start
    while current <= end:
        if _matches_rule(current, rule):
            exists = ClassSession.objects.filter(
                created_from_rule=rule,
                date=current,
                start_time=rule.start_time,
            ).exists()

            if exists:
                skipped += 1
            else:
                ClassSession.objects.create(
                    fitness_class=rule.fitness_class,
                    date=current,
                    start_time=rule.start_time,
                    end_time=rule.end_time,
                    created_from_rule=rule,
                )
                created += 1

        current += timedelta(days=1)

    return created, skipped


def preview_sessions_for_rule(rule, from_date, to_date):
    """
    Dry-run: calculate how many sessions WOULD be created / skipped
    without writing to the database.
    Returns (would_create, would_skip_existing).
    """
    would_create = 0
    would_skip = 0

    start = max(rule.start_date, from_date)
    end = min(rule.end_date or to_date, to_date)

    current = start
    while current <= end:
        if _matches_rule(current, rule):
            exists = ClassSession.objects.filter(
                created_from_rule=rule,
                date=current,
                start_time=rule.start_time,
            ).exists()

            if exists:
                would_skip += 1
            else:
                would_create += 1

        current += timedelta(days=1)

    return would_create, would_skip
