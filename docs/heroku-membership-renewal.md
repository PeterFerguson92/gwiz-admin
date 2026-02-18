# Heroku Setup: Manual Membership Renewal

This guide sets up the current backend behavior on Heroku:
- memberships are monthly
- users renew manually (same purchase flow)
- reminders are sent at 7/3/1 days + expired
- expiry is enforced at cycle end

## 1) Configure required env vars

Replace placeholders and run:

```bash
heroku config:set -a <APP_NAME> \
ENVIROMENT=PROD \
ENABLE_DEBUG=False \
ALLOW_HOSTS=<APP_NAME>.herokuapp.com,<YOUR_DOMAIN> \
CSRF_TRUSTED_ORIGIN=https://<YOUR_DOMAIN> \
PUBLIC_SITE_URL=https://<YOUR_DOMAIN>/ \
MEMBERSHIP_RENEW_URL=https://<YOUR_DOMAIN>/membership \
STRIPE_SECRET_KEY=<sk_live_or_test> \
STRIPE_PUBLISHABLE_KEY=<pk_live_or_test> \
STRIPE_WEBHOOK_SECRET=<whsec_from_stripe_endpoint> \
SENDGRID_API_KEY=<sendgrid_api_key> \
EMAIL_NOTIFICATIONS_ENABLED=True
```

Optional WhatsApp reminders:

```bash
heroku config:set -a <APP_NAME> \
WHATSAPP_NOTIFICATIONS_ENABLED=True \
TWILIO_ACCOUNT_SID=<sid> \
TWILIO_AUTH_TOKEN=<token> \
TWILIO_WHATSAPP_FROM=<e164_number>
```

## 2) Deploy and migrate

```bash
git push heroku main
```

The `release` process runs migrations automatically.

## 3) Add Stripe webhook endpoint (Dashboard)

In Stripe Dashboard:
- Add endpoint: `https://<YOUR_DOMAIN>/api/booking/stripe/webhook/`
- Subscribe at least to:
  - `payment_intent.succeeded`
  - `payment_intent.payment_failed`
  - `payment_intent.canceled`
- Copy signing secret to `STRIPE_WEBHOOK_SECRET`.

## 4) Add daily scheduler job

Install scheduler once:

```bash
heroku addons:create scheduler:standard -a <APP_NAME>
```

In Heroku Dashboard -> Scheduler:
- Add job (daily):

```bash
python manage.py send_membership_reminders
```

Recommended time: morning local business time.

## 5) Smoke test in production

Create a one-off dyno run:

```bash
heroku run -a <APP_NAME> python manage.py send_membership_reminders --dry-run
```

Then run real:

```bash
heroku run -a <APP_NAME> python manage.py send_membership_reminders
```

Verify:
- Admin -> `Membership reminder logs` has rows
- `memberships/me` returns active membership after successful purchase
- renewal emails include full renew URL

## 6) Common failure checks

- `No active membership` after paid checkout:
  - webhook not delivered or wrong `STRIPE_WEBHOOK_SECRET`
- reminders sent with broken links:
  - `MEMBERSHIP_RENEW_URL` missing or not absolute
  - reminder links automatically append `?plan_id=<membership_plan_uuid>`
- no emails:
  - `SENDGRID_API_KEY` missing or sender not verified
