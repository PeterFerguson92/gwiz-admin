import uuid
from django.core.management.base import BaseCommand
from homepage.models import Service
from django.utils.timezone import now

SERVICES = [
    {
        "name": "Strength & Conditioning",
        "short_description": "Build foundational power and endurance with structured strength programming.",
        "long_description": "Push your physical limits with a structured program designed to build functional strength, power, and endurance. From compound lifts to high-intensity circuits, our training will leave you stronger, faster, and more resilient — in and out of the gym.",
    },
    {
        "name": "Flight Crew Group Classes",
        "short_description": "High-energy classes designed to challenge and motivate in a group setting.",
        "long_description": "Energizing, high-impact group workouts that fuel motivation and community. Each class blends challenge and fun, led by our elite crew of coaches. Whether you're new or seasoned, you'll sweat, grow, and never go it alone.",
    },
    {
        "name": "1-on-1 Personal Training",
        "short_description": "Customized training plans and coaching tailored to your goals.",
        "long_description": "Experience the power of personalized coaching. Our one-on-one sessions are tailored to your goals, fitness level, and lifestyle. Get expert guidance, progress tracking, and the accountability you need to unlock your next level.",
    },
    {
        "name": "Athlete Development",
        "short_description": "Performance-focused training for youth and adult athletes.",
        "long_description": "Built for athletes hungry to level up. We train for speed, agility, power, and injury resilience. Ideal for youth and adult athletes chasing scholarships, season readiness, or simply peak performance in their sport.",
    },
    {
        "name": "Flight Check: Fitness Assessments",
        "short_description": "Baseline testing to evaluate your fitness level and track improvements.",
        "long_description": "Know where you stand. Our Flight Check assessments include strength, mobility, endurance, and composition metrics. Benchmark your baseline, track your progress, and stay data-driven in your fitness journey.",
    },
    {
        "name": "Mindset & Recovery Coaching",
        "short_description": "Mental fitness, recovery planning, and accountability coaching.",
        "long_description": "Fitness isn’t just physical — it’s mental. Build the habits, recovery strategies, and internal resilience you need to stay sharp, focused, and sustainable. Learn to rest hard, recover smart, and show up at your best.",
    },
    {
        "name": "Nutrition Coaching",
        "short_description": "Personalized nutrition plans to complement your training.",
        "long_description": "Fuel your performance with smarter nutrition. Our coaches work with your lifestyle to craft custom plans focused on muscle gain, fat loss, energy, and longevity. No fads — just results-driven eating that fits you.",
    },
    {
        "name": "Workshops & Events",
        "short_description": "Special events and intensives led by expert coaches and guests.",
        "long_description": "Level up your skills and mindset in immersive weekend intensives and specialty events. From lifting clinics to mindset summits, you'll get expert insight, hands-on training, and a surge of community energy.",
    },
    {
        "name": "Online Coaching & Programming",
        "short_description": "Train with us from anywhere with remote plans and virtual check-ins.",
        "long_description": "Train with the Flight School Chamber Gang no matter where you are. Get remote coaching, weekly check-ins, customized plans, and access to our digital platform. Perfect for the self-driven athlete or traveler.",
    },
]

class Command(BaseCommand):
    help = "Seed the database with Flight School Chamber Gang services"

    def handle(self, *args, **kwargs):
        for service in SERVICES:
            obj, created = Service.objects.get_or_create(
                name=service["name"],
                defaults={
                    "id": uuid.uuid4(),
                    "short_description": service["short_description"],
                    "long_description": service["long_description"],
                    "created_at": now(),
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✔ Created: {obj.name}"))
            else:
                self.stdout.write(f"⏩ Skipped (already exists): {obj.name}")
