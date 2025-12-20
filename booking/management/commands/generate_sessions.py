from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import models

from booking.models import ClassSession, RecurrenceRule

WEEKDAY_CODE_BY_INDEX = {
    0: "mon",
    1: "tue",
    2: "wed",
    3: "thu",
    4: "fri",
    5: "sat",
    6: "sun",
}


class Command(BaseCommand):
    help = "Generate ClassSession instances from active RecurrenceRule objects."

    def add_arguments(self, parser):
        parser.add_argument(
            "--from-date",
            type=str,
            help="Start date (inclusive) in YYYY-MM-DD format. Defaults to today.",
        )
        parser.add_argument(
            "--to-date",
            type=str,
            help="End date (inclusive) in YYYY-MM-DD format. "
            "If omitted, --days is used.",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days from from-date to generate sessions for "
            "if --to-date is not provided (default: 30).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without writing to the database.",
        )

    def handle(self, *args, **options):
        from_date_str = options.get("from_date")
        to_date_str = options.get("to_date")
        days = options.get("days") or 30
        dry_run = options.get("dry_run", False)

        # Determine date range
        if from_date_str:
            from_date = date.fromisoformat(from_date_str)
        else:
            from_date = date.today()

        if to_date_str:
            to_date = date.fromisoformat(to_date_str)
        else:
            to_date = from_date + timedelta(days=days)

        if to_date < from_date:
            self.stderr.write(self.style.ERROR("to-date cannot be before from-date"))
            return

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"Generating sessions from {from_date} to {to_date} "
                f"({'dry-run' if dry_run else 'apply'})"
            )
        )

        rules_qs = RecurrenceRule.objects.filter(
            is_active=True,
            start_date__lte=to_date,
        ).filter(models.Q(end_date__isnull=True) | models.Q(end_date__gte=from_date))

        if not rules_qs.exists():
            self.stdout.write(self.style.WARNING("No active recurrence rules found."))
            return

        total_created = 0
        total_skipped_existing = 0

        for rule in rules_qs.select_related("fitness_class"):
            created_for_rule, skipped_for_rule = self._process_rule(
                rule, from_date, to_date, dry_run
            )
            total_created += created_for_rule
            total_skipped_existing += skipped_for_rule

            self.stdout.write(
                f"- Rule for '{rule.fitness_class.name}' "
                f"({rule.recurrence_type}): created {created_for_rule}, "
                f"skipped {skipped_for_rule}"
            )

        self.stdout.write("")
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] Would create {total_created} sessions, "
                    f"skipped {total_skipped_existing} existing"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {total_created} sessions, "
                    f"skipped {total_skipped_existing} existing"
                )
            )

    def _process_rule(self, rule, from_date, to_date, dry_run=False):
        """
        For a single RecurrenceRule, find all dates in [from_date, to_date]
        that match the rule and create ClassSession objects when needed.
        """
        # Clamp date range to the rule's active range
        rule_start = max(rule.start_date, from_date)
        rule_end = to_date
        if rule.end_date:
            rule_end = min(rule.end_date, to_date)

        if rule_end < rule_start:
            return 0, 0  # no overlap

        created = 0
        skipped_existing = 0

        current_date = rule_start
        while current_date <= rule_end:
            if self._date_matches_rule(current_date, rule):
                # Avoid duplicates: check if a session already exists
                exists = ClassSession.objects.filter(
                    created_from_rule=rule,
                    date=current_date,
                    start_time=rule.start_time,
                ).exists()

                if exists:
                    skipped_existing += 1
                else:
                    if not dry_run:
                        ClassSession.objects.create(
                            fitness_class=rule.fitness_class,
                            date=current_date,
                            start_time=rule.start_time,
                            end_time=rule.end_time,
                            created_from_rule=rule,
                        )
                    created += 1

            current_date += timedelta(days=1)

        return created, skipped_existing

    def _date_matches_rule(self, current_date, rule):
        """
        Decide whether a given date matches the given recurrence rule.
        """
        if rule.recurrence_type == "one_off":
            return current_date == rule.start_date

        if rule.recurrence_type == "daily":
            return True

        weekday_code = WEEKDAY_CODE_BY_INDEX[current_date.weekday()]

        if rule.recurrence_type in ("weekly", "multi_weekly"):
            # If no days_of_week are set, treat as nothing matches
            if not rule.days_of_week:
                return False
            return weekday_code in rule.days_of_week

        # Fallback: no match
        return False
