"""
Email service for Zomato Notes.

Sends password-reset emails via SMTP.
Supports two modes:
  - Real SMTP (SMTP_HOST set in env) — uses Brevo/Gmail/any SMTP server
  - Console mode (SMTP_HOST not set) — prints the reset link to logs
    so the app still works without an email provider configured.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

# ── Config (all optional — falls back to console mode) ───────────────────────
SMTP_HOST     = os.getenv("SMTP_HOST", "")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM    = os.getenv("EMAIL_FROM", SMTP_USER)
FRONTEND_URL  = os.getenv("FRONTEND_URL", "https://amitydv2026.github.io/Zomato-Notes-Project")


def send_reset_email(to_email: str, to_name: str, reset_token: str) -> bool:
    """
    Send a password-reset email.

    Returns True on success, False on failure.
    If SMTP is not configured, logs the link instead (console mode).
    """
    reset_url = f"{FRONTEND_URL}/auth.html?reset={reset_token}"

    # ── HTML email body ───────────────────────────────────────────────────────
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
    .container {{ max-width: 480px; margin: 0 auto; background: #fff; border-radius: 12px;
                  box-shadow: 0 4px 20px rgba(0,0,0,0.08); overflow: hidden; }}
    .header {{ background: linear-gradient(135deg, #e23744, #c0303b); padding: 28px 32px; text-align: center; }}
    .header h1 {{ color: #fff; margin: 0; font-size: 1.4rem; font-weight: 800; }}
    .header p  {{ color: rgba(255,255,255,0.85); margin: 6px 0 0; font-size: 0.85rem; }}
    .body {{ padding: 32px; }}
    .body p {{ color: #374151; line-height: 1.6; margin: 0 0 16px; }}
    .btn {{ display: block; width: fit-content; margin: 24px auto; padding: 14px 32px;
            background: #e23744; color: #fff !important; border-radius: 8px;
            text-decoration: none; font-weight: 700; font-size: 1rem; text-align: center; }}
    .note {{ font-size: 0.8rem; color: #9ca3af; text-align: center; margin-top: 20px; line-height: 1.5; }}
    .url-box {{ background: #f3f4f6; border-radius: 6px; padding: 10px 14px; word-break: break-all;
                font-size: 0.78rem; color: #6b7280; margin-top: 12px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>📝 Zomato Notes</h1>
      <p>Password Reset Request</p>
    </div>
    <div class="body">
      <p>Hi <strong>{to_name}</strong>,</p>
      <p>We received a request to reset your Zomato Notes password.
         Click the button below to choose a new password:</p>
      <a class="btn" href="{reset_url}">Reset My Password</a>
      <p>This link expires in <strong>30 minutes</strong>. If you didn't request a
         password reset, you can safely ignore this email — your password won't change.</p>
      <div class="url-box">Or copy this link: {reset_url}</div>
      <p class="note">For security, this link can only be used once.<br>
         If you need help, contact your admin.</p>
    </div>
  </div>
</body>
</html>
"""

    plain_body = (
        f"Hi {to_name},\n\n"
        f"Reset your Zomato Notes password by visiting:\n{reset_url}\n\n"
        f"This link expires in 30 minutes and can only be used once.\n\n"
        f"If you didn't request this, ignore this email."
    )

    # ── Console mode (no SMTP configured) ────────────────────────────────────
    if not SMTP_HOST:
        logger.info(
            f"\n{'='*60}\n"
            f"[PASSWORD RESET — CONSOLE MODE]\n"
            f"To: {to_email}\n"
            f"Reset URL: {reset_url}\n"
            f"{'='*60}"
        )
        return True   # pretend success so the frontend shows the right message

    # ── Real SMTP send ────────────────────────────────────────────────────────
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Reset your Zomato Notes password"
        msg["From"]    = f"Zomato Notes <{EMAIL_FROM}>"
        msg["To"]      = to_email

        msg.attach(MIMEText(plain_body, "plain"))
        msg.attach(MIMEText(html_body,  "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, to_email, msg.as_string())

        logger.info(f"Password reset email sent to {to_email}")
        return True

    except Exception as exc:
        logger.error(f"Failed to send reset email to {to_email}: {exc!r}")
        return False
