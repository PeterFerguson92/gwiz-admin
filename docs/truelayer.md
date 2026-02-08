# TrueLayer Payments (Hosted Payment Page)

This project supports TrueLayer alongside Stripe for class bookings and event tickets.
TrueLayer payments are created via the Hosted Payment Page (HPP) flow.

## Environment variables

```
TRUE_LAYER_CLIENT_ID=...
TRUE_LAYER_KEY_ID=...
TRUE_LAYER_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
TRUE_LAYER_MERCHANT_ACCOUNT_ID=...
TRUE_LAYER_API_BASE=https://payment.truelayer.com
TRUE_LAYER_AUTH_AUDIENCE=https://payment.truelayer.com
TRUE_LAYER_RETURN_URL=https://<your-frontend>/payment/return
TRUE_LAYER_WEBHOOK_SIGNING_KEY=... (public key PEM, optional but recommended)
TRUE_LAYER_WEBHOOK_TOLERANCE_SEC=300 (optional)
```

## Booking / Event flow

1. Client passes `payment_provider=truelayer` to:
   - `POST /api/booking/sessions/<session_id>/book/`
   - `POST /api/events/<event_id>/tickets/`
2. API returns `truelayer_authorization_url`.
3. Client redirects the user to the HPP URL.
4. TrueLayer calls back to:
   - `POST /api/booking/truelayer/webhook/`
   - `POST /api/events/truelayer/webhook/`
5. On success (`executed`/`settled`) we mark the booking/ticket as paid.
   On failure (`failed`/`cancelled`/`expired`) we void/cancel.

## Notes

- Webhook signature verification is enabled when TRUE_LAYER_WEBHOOK_SIGNING_KEY is set.
- The handler also checks the webhook timestamp header when present.

## Webhook test harness

We include a management command to validate webhook signatures locally before
the TrueLayer console is fully configured. This prevents guesswork when you
start receiving live webhooks.

Command:

```
python manage.py verify_truelayer_webhook \
  --payload /path/to/webhook.json \
  --signature "<TL-Signature>" \
  --timestamp "2026-02-08T12:00:00Z"
```

Why it exists:
- Confirms your `TRUE_LAYER_WEBHOOK_SIGNING_KEY` is correct.
- Ensures the same verification logic used by webhooks is working.
- The return URL should be a frontend route that shows the "processing" state;
  it should not be trusted as payment confirmation.
