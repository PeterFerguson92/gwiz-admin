# WhatsApp Notifications

The booking workflow now sends WhatsApp messages through Twilio when:

- a booking is confirmed (membership credit or Stripe payment success), and
- a booking is cancelled (user cancellation or failed Stripe payment).

## Twilio setup

1. Enable the WhatsApp channel for your Twilio number or messaging service.
2. Create two approved WhatsApp templates in Twilio Content Builder (or the Legacy
   Template section) – one for confirmations and one for cancellations.
   Each template should expose four variables in order:
   1. member name
   2. class name
   3. session date (e.g. `Mon 09 Dec 2025`)
   4. session start time (e.g. `18:30`)
3. Note the generated template/content SIDs.

## Environment variables

Add the following to `dev.env` / `prod.env` and restart the Django app:

```
WHATSAPP_NOTIFICATIONS_ENABLED=True
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=********************************
TWILIO_WHATSAPP_FROM=+441234567890
TWILIO_WHATSAPP_CONFIRM_TEMPLATE_SID=HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_CANCEL_TEMPLATE_SID=HXyyyyyyyyyyyyyyyyyyyyyyyyyyyy
TWILIO_WHATSAPP_ADMIN_RECIPIENTS=+441234567890,+441234567891
TWILIO_WHATSAPP_ADMIN_TEMPLATE_SID=HXadminStatusZZZZZZZZZZZZ
```

`TWILIO_WHATSAPP_FROM` must be the raw E.164 number (the code automatically
prefixes it with `whatsapp:`). The helper falls back to sending plain-text bodies
if a template SID is missing, but Meta will reject those outside the 24‑hour
session window—only template sends will clear that restriction.

`TWILIO_WHATSAPP_ADMIN_RECIPIENTS` is a comma‑separated list of numbers that
should receive booking status alerts (confirmations and cancellations). Those
messages include the member name, class/date/time, and the updated count of
booked spots so owners always know session fill levels. Create a single admin
template (`TWILIO_WHATSAPP_ADMIN_TEMPLATE_SID`) with six variables in this order:

1. event label (`confirmed` / `cancelled`)
2. member name
3. class name
4. session date
5. session time
6. bookings summary (e.g. `12/18`)
