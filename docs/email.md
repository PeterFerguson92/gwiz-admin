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
