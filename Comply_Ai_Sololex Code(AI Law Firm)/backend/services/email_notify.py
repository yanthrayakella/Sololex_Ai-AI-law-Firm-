import logging
import smtplib
from email.message import EmailMessage

from config import settings

logger = logging.getLogger(__name__)


def send_alert_email(
    to_email: str,
    regulation_title: str,
    contract_name: str,
    clause_description: str,
    penalty_amount: str,
    action_required: str,
) -> None:
    body = f"""Your contract "{contract_name}" is affected by a new regulation.

Issue: {clause_description}
Risk: {penalty_amount}
Required Action: {action_required}

Login to fix: {settings.dashboard_base_url}/dashboard
"""
    if not settings.smtp_host:
        logger.info(
            "SMTP not configured; would email %s — regulation=%s contract=%s",
            to_email,
            regulation_title,
            contract_name,
        )
        logger.debug(body)
        return

    msg = EmailMessage()
    msg["Subject"] = f"[ComplyAI] Contract Alert: {regulation_title}"
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
        smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)
