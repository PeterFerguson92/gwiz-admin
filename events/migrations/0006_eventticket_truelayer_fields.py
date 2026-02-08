from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0005_eventticket_is_guest_purchase"),
    ]

    operations = [
        migrations.AddField(
            model_name="eventticket",
            name="payment_provider",
            field=models.CharField(
                choices=[
                    ("included", "Included"),
                    ("stripe", "Stripe"),
                    ("truelayer", "TrueLayer"),
                ],
                default="stripe",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="eventticket",
            name="truelayer_payment_id",
            field=models.CharField(
                blank=True,
                help_text="TrueLayer payment ID for paid tickets.",
                max_length=255,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="eventticket",
            name="truelayer_payment_status",
            field=models.CharField(
                blank=True,
                help_text="Last known TrueLayer payment status.",
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name="eventticket",
            name="truelayer_payment_reference",
            field=models.CharField(
                blank=True,
                help_text="Reference sent to TrueLayer for reconciliation.",
                max_length=100,
            ),
        ),
    ]
