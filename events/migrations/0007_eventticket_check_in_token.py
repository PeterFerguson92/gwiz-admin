import uuid

from django.db import migrations, models


def populate_event_ticket_check_in_tokens(apps, schema_editor):
    EventTicket = apps.get_model("events", "EventTicket")

    for ticket in EventTicket.objects.filter(check_in_token__isnull=True).iterator():
        ticket.check_in_token = uuid.uuid4()
        ticket.save(update_fields=["check_in_token"])


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0006_eventticket_checked_in_at_eventticket_checked_in_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="eventticket",
            name="check_in_token",
            field=models.UUIDField(blank=True, editable=False, null=True),
        ),
        migrations.RunPython(
            populate_event_ticket_check_in_tokens,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="eventticket",
            name="check_in_token",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
