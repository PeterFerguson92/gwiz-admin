import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand

from events.models import Event


class Command(BaseCommand):
    help = "Seed a few sample events for local development/testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Create events even if names already exist (will append a suffix).",
        )

    def handle(self, *args, **options):
        now = datetime.datetime.now()

        samples = [
            {
                "name": "Summer Shred Bootcamp",
                "description": "High-intensity group workout to kickstart your summer goals.",
                "location": "Main Gym Floor",
                "start_datetime": now + datetime.timedelta(days=7, hours=18),
                "end_datetime": now + datetime.timedelta(days=7, hours=19, minutes=30),
                "ticket_price": Decimal("15.00"),
                "capacity": 30,
                "is_active": True,
                "is_featured": True,
                "featured_order": 1,
            },
            {
                "name": "Mobility & Recovery Workshop",
                "description": "Learn foam rolling, stretching, and recovery best practices.",
                "location": "Studio B",
                "start_datetime": now + datetime.timedelta(days=10, hours=17),
                "end_datetime": now + datetime.timedelta(days=10, hours=18, minutes=15),
                "ticket_price": Decimal("0.00"),  # free
                "capacity": 20,
                "is_active": True,
                "is_featured": True,
                "featured_order": 2,
            },
            {
                "name": "Kettlebell Fundamentals",
                "description": "A primer on safe kettlebell technique: swings, cleans, snatches.",
                "location": "Studio A",
                "start_datetime": now + datetime.timedelta(days=14, hours=18),
                "end_datetime": now + datetime.timedelta(days=14, hours=19),
                "ticket_price": Decimal("12.00"),
                "capacity": 18,
                "is_active": True,
                "is_featured": False,
                "featured_order": 3,
            },
        ]

        created = 0
        for data in samples:
            name = data["name"]
            if options["force"]:
                base_name = name
                suffix = 1
                while Event.objects.filter(name=name).exists():
                    suffix += 1
                    name = f"{base_name} ({suffix})"
                data["name"] = name
                Event.objects.create(**data)
                created += 1
                self.stdout.write(self.style.SUCCESS(f"Created event '{name}'"))
            else:
                obj, was_created = Event.objects.get_or_create(
                    name=name,
                    defaults=data,
                )
                if was_created:
                    created += 1
                    self.stdout.write(self.style.SUCCESS(f"Created event '{name}'"))
                else:
                    self.stdout.write(f"Skipped existing event '{name}'")

        self.stdout.write(self.style.SUCCESS(f"Done. Created {created} events."))
