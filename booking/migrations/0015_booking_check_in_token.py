import uuid

from django.db import migrations, models


def populate_booking_check_in_tokens(apps, schema_editor):
    Booking = apps.get_model("booking", "Booking")

    for booking in Booking.objects.filter(check_in_token__isnull=True).iterator():
        booking.check_in_token = uuid.uuid4()
        booking.save(update_fields=["check_in_token"])


class Migration(migrations.Migration):
    dependencies = [
        ("booking", "0014_booking_checked_in_at_booking_checked_in_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="check_in_token",
            field=models.UUIDField(blank=True, editable=False, null=True),
        ),
        migrations.RunPython(
            populate_booking_check_in_tokens,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="booking",
            name="check_in_token",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
