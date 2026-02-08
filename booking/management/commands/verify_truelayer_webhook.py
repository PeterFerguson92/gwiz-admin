import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from gwiz_admin import truelayer


class Command(BaseCommand):
    help = (
        "Verify a TrueLayer webhook payload/signature using the configured public key."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--payload", required=True, help="Path to JSON payload file."
        )
        parser.add_argument(
            "--signature", required=True, help="TL-Signature header value."
        )
        parser.add_argument(
            "--timestamp",
            required=False,
            help="X-TL-Webhook-Timestamp header value (optional).",
        )

    def handle(self, *args, **options):
        payload_path = Path(options["payload"])
        if not payload_path.exists():
            raise CommandError(f"Payload file not found: {payload_path}")

        try:
            payload_bytes = payload_path.read_bytes()
            json.loads(payload_bytes.decode("utf-8"))
        except Exception as exc:
            raise CommandError(f"Invalid JSON payload: {exc}") from exc

        signature = options["signature"]
        timestamp = options.get("timestamp")

        valid = truelayer.verify_webhook(signature, timestamp, payload_bytes)
        if not valid:
            raise CommandError("Signature verification failed.")

        self.stdout.write(self.style.SUCCESS("Signature verification passed."))
