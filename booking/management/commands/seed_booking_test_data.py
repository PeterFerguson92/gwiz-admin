import datetime
import random

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from booking.models import Booking, ClassSession, FitnessClass, RecurrenceRule
from homepage.models import Trainer


class Command(BaseCommand):
    help = "Seed test data for booking system"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Seeding Booking Test Data..."))

        # -------------------------
        # 1. Trainers
        # -------------------------
        trainers = []
        trainer_names = ["Alice", "Bobby", "Carla", "Dan", "Eva"]

        for name in trainer_names:
            trainer, _ = Trainer.objects.get_or_create(
                full_name=name,
                defaults={"bio": f"{name} is a certified fitness coach."},
            )
            trainers.append(trainer)

        # -------------------------
        # 2. Fitness Classes
        # -------------------------
        classes_data = [
            ("Beginner Yoga", "Relaxing intro yoga class", "yoga", 12),
            ("HIIT Blast", "High intensity interval training", "cardio", 15),
            ("Strength Circuit", "Full body strength class", "strength", 14),
        ]

        fitness_classes = []

        for name, desc, genre, price in classes_data:
            fc, _ = FitnessClass.objects.get_or_create(
                name=name,
                defaults={
                    "description": desc,
                    "genre": genre,
                    "base_price": price,
                    "default_duration_minutes": 60,
                    "capacity": random.choice([12, 15, 20]),
                    "is_active": True,
                },
            )
            # assign random trainers
            fc.instructors.set(random.sample(trainers, k=random.randint(1, 2)))
            fitness_classes.append(fc)

        # -------------------------
        # 3. Recurrence rules + generate sessions
        # -------------------------
        RecurrenceRule.objects.all().delete()  # reset test rules
        ClassSession.objects.all().delete()  # reset test sessions

        today = datetime.date.today()

        for fc in fitness_classes:
            rule = RecurrenceRule.objects.create(
                fitness_class=fc,
                recurrence_type="weekly",
                days_of_week=["mon", "wed", "fri"],
                start_time=datetime.time(18, 0),
                end_time=datetime.time(19, 0),
                start_date=today,
                end_date=today + datetime.timedelta(days=60),
            )

            # generate sessions for next 30 days
            for i in range(0, 30):
                d = today + datetime.timedelta(days=i)
                if d.strftime("%a").lower()[:3] in rule.days_of_week:
                    ClassSession.objects.create(
                        fitness_class=fc,
                        date=d,
                        start_time=rule.start_time,
                        end_time=rule.end_time,
                        created_from_rule=rule,
                        status="scheduled",
                    )

        # -------------------------
        # 4. Test User
        # -------------------------
        user, created = User.objects.get_or_create(
            email="testuser@example.com",
            defaults={"full_name": "Test User"},
        )
        if created:
            user.set_password("password123")
            user.save()

        # -------------------------
        # 5. Add Bookings
        # -------------------------
        all_sessions = list(ClassSession.objects.all())

        # book 5 random sessions
        for session in random.sample(all_sessions, k=5):
            Booking.objects.get_or_create(
                user=user,
                class_session=session,
                defaults={
                    "status": Booking.STATUS_BOOKED,
                    "payment_status": Booking.PAYMENT_INCLUDED,
                },
            )

        self.stdout.write(
            self.style.SUCCESS("✔ Test booking data created successfully!")
        )
