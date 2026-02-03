# Stripe Integration Overview

The booking API can now create and manage card payments via Stripe. This quick reference
summarises what needs to be configured in each environment and how to test locally.

## Configuration

Set the following environment variables (already stubbed in `dev.env` / `prod.env`):

| Variable | Purpose |
| --- | --- |
| `STRIPE_SECRET_KEY` | Server-side API key (e.g. `sk_test_xxx`). |
| `STRIPE_PUBLISHABLE_KEY` | Key exposed to the frontend for Stripe.js. |
| `STRIPE_WEBHOOK_SECRET` | Secret used to verify webhook payloads (`stripe listen ...`). |
| `STRIPE_CURRENCY` | ISO currency code used for PaymentIntents (`gbp` by default). |
| `STRIPE_PAYMENT_DESCRIPTION_PREFIX` | Optional label prefixed in PaymentIntent descriptions. |

## Booking Flow

1. When a member does *not* have credits, `POST /api/booking/sessions/<session_id>/book/`
   responds with the normal booking payload plus a `stripe_client_secret`.
2. The frontend should call `stripe.confirmPayment` with that client secret.
3. Successful confirmations trigger Stripe to send `payment_intent.succeeded` to
   `/api/booking/stripe/webhook/`, which marks the booking as `paid`.

If Stripe keys are missing the API short-circuits and returns a 503, so the frontend can fall
back to an alternative checkout if needed.

## Local Testing

```bash
pip install -r requirements.txt
stripe login
stripe listen --forward-to localhost:8000/api/booking/stripe/webhook/
export STRIPE_SECRET_KEY=sk_test_xxx
export STRIPE_PUBLISHABLE_KEY=pk_test_xxx
export STRIPE_WEBHOOK_SECRET=$(stripe listen --print-secret)
python manage.py runserver
```

### Handy reference

- `stripe listen --forward-to localhost:8000/api/booking/stripe/webhook/`
- Copy the signing secret the CLI prints and put it into `STRIPE_WEBHOOK_SECRET` (or
  export it temporarily) before starting `runserver`.
- Make sure the CLI stays running in its own terminal while you test, otherwise the
  `payment_intent.succeeded` event never reaches Django and WhatsApp confirmations
  for card bookings will not fire.

Use test card numbers (e.g. `4242 4242 4242 4242`) when Stripe.js collects the payment
details. The webhook endpoint automatically frees the booking and voids payment if a
PaymentIntent fails or is cancelled.





python manage.py expire_pending_bookings --minutes 30
