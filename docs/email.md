# Email & Password Reset

Password reset emails are now sent through the SendGrid HTTP API using
`notifications.email.send_password_reset_email`. This avoids relying on the
default Django SMTP backend and provides delivery logs directly within SendGrid.

## Configuration

1. Set `SENDGRID_API_KEY` in the environment (`dev.env` / `prod.env`). The key
   must have permission to use the Mail Send API.
2. Ensure `DEFAULT_FROM_EMAIL` contains a verified sender address in SendGrid
   (e.g. `Fsxcg <no-reply@fsxcg.com>`).
3. Restart Django after updating the environment so the cached SendGrid client
   picks up the new settings.
4. Set `FRONTEND_RESET_PASSWORD_URL` to the frontend route that handles reset
   links (e.g. `https://app.fsxcg.com/reset-password` or your local dev URL).

## Local testing

```bash
pip install -r requirements.txt
export SENDGRID_API_KEY=SG.xxxxx
python manage.py shell
```

Then trigger `PasswordResetRequestView` via the API or call
`send_password_reset_email` manually from the shell. Check SendGrid's Activity
log to confirm the email was accepted. Any failures are logged via the
`notifications.email` logger, so run the server with `DEBUG=True` to see them on
stdout.

## Brevo per-flow overrides (optional)

Brevo REST support is additive and SendGrid remains the default provider.

```bash
export BREVO_API_KEY=your_brevo_api_key
export EMAIL_PROVIDER=sendgrid
export EMAIL_PROVIDER_EVENTS=brevo
# optional:
# export EMAIL_PROVIDER_PASSWORD_RESET=brevo
# export EMAIL_PROVIDER_BOOKING=brevo
```

### Brevo template IDs

```bash
export BREVO_TEMPLATE_ID_PASSWORD_RESET=111
export BREVO_TEMPLATE_ID_BOOKING=222
export BREVO_TEMPLATE_ID_MEMBERSHIP=333
export BREVO_TEMPLATE_ID_EVENTS=444
```

### Brevo template params expected by flow

- `password reset`: `user_name`, `reset_url`
- `booking confirmation`: `class_name`, `class_id`, `session_date`, `start_time`, `end_time`, `booking_id`, `status`, `payment_status`, `cancel_url`, `class_url`, `logo_url`, `header_banner_url`, `subject`
- `membership reminder`: `user_name`, `lead_text`, `plan_name`, `reset_label`, `renew_url`, `subject`
- `events`: `event_name`, `location`, `starts_at`, `ends_at`, `quantity`, `ticket_id`, `event_id`, `user_email`, `status`, `payment_status`, `logo_url`, `header_banner_url`, `subject`, optional `cancel_url`
