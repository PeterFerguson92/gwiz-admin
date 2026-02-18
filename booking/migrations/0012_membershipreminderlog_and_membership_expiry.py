import uuid

from django.db import migrations, models


def backfill_membership_expires_at(apps, schema_editor):
    UserMembership = apps.get_model("booking", "UserMembership")
    for membership in UserMembership.objects.filter(
        next_reset_at__isnull=False,
        expires_at__isnull=True,
    ):
        membership.expires_at = membership.next_reset_at
        membership.save(update_fields=["expires_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("booking", "0011_usermembership_next_reset_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="MembershipReminderLog",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "reminder_type",
                    models.CharField(
                        choices=[
                            ("renew_7_days", "Renewal reminder (7 days)"),
                            ("renew_3_days", "Renewal reminder (3 days)"),
                            ("renew_1_day", "Renewal reminder (1 day)"),
                            ("expired", "Membership expired"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "cycle_reset_at",
                    models.DateTimeField(
                        help_text="The reset/expiry boundary this reminder belongs to."
                    ),
                ),
                ("email_sent", models.BooleanField(default=False)),
                ("whatsapp_sent", models.BooleanField(default=False)),
                ("sent_at", models.DateTimeField(auto_now_add=True)),
                (
                    "membership",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="reminder_logs",
                        to="booking.usermembership",
                    ),
                ),
            ],
            options={
                "ordering": ("-sent_at",),
                "constraints": [
                    models.UniqueConstraint(
                        fields=("membership", "reminder_type", "cycle_reset_at"),
                        name="unique_membership_reminder_per_cycle",
                    )
                ],
            },
        ),
        migrations.RunPython(backfill_membership_expires_at, migrations.RunPython.noop),
    ]
