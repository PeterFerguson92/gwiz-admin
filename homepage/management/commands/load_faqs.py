import uuid

from django.core.management.base import BaseCommand
from django.utils.timezone import now

from homepage.models import Faq

FAQS = [
    {
        "question": "What’s the best way to get started if I’m new?",
        "answer": "We recommend booking a free consultation or trying out a Flight Crew group class. Our coaches will assess your goals and help guide you into the right training path — no pressure, just progress.",
    },
    {
        "question": "Do I need to be 'in shape' before I join?",
        "answer": "Absolutely not. We meet you where you are. Whether you’re brand new or a seasoned athlete, our programs scale to your level — and you’ll grow stronger every session.",
    },
    {
        "question": "What’s the difference between personal training and group classes?",
        "answer": "Personal training is one-on-one, customized coaching with a focus entirely on you. Group classes deliver high-energy, coach-led workouts with a team vibe — perfect if you thrive on community.",
    },
    {
        "question": "Is nutrition coaching included?",
        "answer": "Nutrition is offered as an add-on service. Our coaches create realistic, sustainable plans tailored to your lifestyle — whether you’re focused on performance, weight loss, or energy.",
    },
    {
        "question": "Can I train remotely?",
        "answer": "Yes! Our online coaching program includes personalized workouts, check-ins, and accountability — ideal if you're on the go or outside the city.",
    },
]


class Command(BaseCommand):
    help = "Seed initial FAQ entries for Flight School Chamber Gang"

    def handle(self, *args, **kwargs):
        for faq in FAQS:
            obj, created = Faq.objects.get_or_create(
                question=faq["question"],
                defaults={
                    "id": uuid.uuid4(),
                    "answer": faq["answer"],
                    "created_at": now(),
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✔ Created: {obj.question}"))
