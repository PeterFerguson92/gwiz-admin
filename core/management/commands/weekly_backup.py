import subprocess
from datetime import timezone as dt_timezone

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Capture a Heroku Postgres backup weekly on Sunday at 21:00 UTC."

    def handle(self, *args, **options):
        now_utc = timezone.now().astimezone(dt_timezone.utc)

        is_sunday = now_utc.weekday() == 6
        is_backup_window = now_utc.hour == 21 and now_utc.minute < 10

        if not (is_sunday and is_backup_window):
            self.stdout.write(
                self.style.WARNING(
                    f"Skipping backup at {now_utc.isoformat()} (requires Sunday 21:00 UTC, minute < 10)."
                )
            )
            return

        command = ["heroku", "pg:backups:capture", "--app", "gwiz-admin"]
        self.stdout.write(
            self.style.NOTICE(
                f"Running weekly backup at {now_utc.isoformat()}: {' '.join(command)}"
            )
        )

        result = subprocess.run(command, check=False, capture_output=True, text=True)

        if result.stdout:
            self.stdout.write(result.stdout.strip())
        if result.stderr:
            self.stderr.write(result.stderr.strip())

        if result.returncode == 0:
            self.stdout.write(
                self.style.SUCCESS("Weekly backup completed successfully.")
            )
            return

        raise SystemExit(result.returncode)
