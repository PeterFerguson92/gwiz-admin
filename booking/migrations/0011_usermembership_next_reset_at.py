from django.db import migrations, models


def backfill_next_reset_at(apps, schema_editor):
    UserMembership = apps.get_model("booking", "UserMembership")
    for membership in UserMembership.objects.filter(next_reset_at__isnull=True):
        starts_at = membership.starts_at
        year = starts_at.year + (starts_at.month // 12)
        month = 1 if starts_at.month == 12 else starts_at.month + 1
        # Day clamp for short months.
        if month == 2:
            if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                max_day = 29
            else:
                max_day = 28
        elif month in (4, 6, 9, 11):
            max_day = 30
        else:
            max_day = 31
        day = min(starts_at.day, max_day)
        membership.next_reset_at = starts_at.replace(year=year, month=month, day=day)
        membership.save(update_fields=["next_reset_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("booking", "0010_update_booking_unique_constraint"),
    ]

    operations = [
        migrations.AddField(
            model_name="usermembership",
            name="next_reset_at",
            field=models.DateTimeField(
                blank=True,
                help_text="When monthly credits should next reset.",
                null=True,
            ),
        ),
        migrations.RunPython(backfill_next_reset_at, migrations.RunPython.noop),
    ]
