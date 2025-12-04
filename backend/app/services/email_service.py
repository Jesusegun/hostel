"""
Email service for transactional notifications using SMTP.
"""

from __future__ import annotations

import logging
import smtplib
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict

from app.config import settings

logger = logging.getLogger(__name__)


def _format_resolution_email(issue: Dict[str, Any], reopen_link: str) -> Dict[str, str]:
    hall = issue.get("hall_name") or "Hall"
    room = issue.get("room_number") or "N/A"
    category = issue.get("category_name") or "General"
    subject = f"Issue resolved – {hall} • Room {room}"
    student_name = issue.get('student_name') or 'Student'
    
    html_body = f"""
    <p>Dear {student_name},</p>
    <p>Your hostel repair request for <strong>{hall}</strong> (room <strong>{room}</strong>, category: {category})
    has been marked as <strong>Done</strong>.</p>
    <p>If no work was actually carried out and the issue persists, please click this button to reopen the ticket within the next 72 hours.</p>
    <p style="margin:16px 0;">
      <a href="{reopen_link}" style="background:#2563EB;color:#fff;padding:10px 18px;
         border-radius:6px;text-decoration:none;display:inline-block;">
        Reopen complaint
      </a>
    </p>
    <p>Thank you</p>
    """

    text_body = (
        f"Dear {student_name},\n\n"
        f"Your repair request for {hall} (room {room}, category: {category}) was marked as done.\n"
        f"If no work was actually carried out and the issue persists, reopen it within 72 hours: {reopen_link}\n\n"
        "Thank you"
    )

    return {"subject": subject, "html": html_body, "text": text_body}


def send_issue_resolved_email(issue: Dict[str, Any], reopen_link: str) -> None:
    """
    Send a completion email to the student with a reopen CTA.
    """
    issue_id = issue.get("id")
    recipient = issue.get("student_email")
    
    if not recipient:
        logger.warning(
            "Issue %s has no student_email field; skipping resolution email notification",
            issue_id
        )
        return

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            "SMTP_USER or SMTP_PASSWORD not configured in environment; skipping resolution email for issue %s",
            issue_id
        )
        return

    logger.info(
        "Attempting to send resolution email for issue %s to %s",
        issue_id,
        recipient[:3] + "***" if len(recipient) > 3 else "***"
    )

    template = _format_resolution_email(issue, reopen_link)

    try:
        _send_with_smtp(recipient, template)
        logger.info(
            "Resolution email sent successfully for issue %s to %s",
            issue_id,
            recipient[:3] + "***" if len(recipient) > 3 else "***"
        )
    except smtplib.SMTPAuthenticationError as exc:
        logger.error(
            "SMTP authentication error sending resolution email for issue %s: %s",
            issue_id,
            str(exc)
        )
    except smtplib.SMTPConnectError as exc:
        logger.error(
            "SMTP connection error sending resolution email for issue %s: %s",
            issue_id,
            str(exc)
        )
    except smtplib.SMTPException as exc:
        logger.error(
            "SMTP error sending resolution email for issue %s: %s",
            issue_id,
            str(exc)
        )
    except socket.error as exc:
        logger.error(
            "Network error sending resolution email for issue %s: %s",
            issue_id,
            str(exc)
        )
    except Exception as exc:
        logger.error(
            "Unexpected error sending resolution email for issue %s: %s",
            issue_id,
            exc,
            exc_info=True
        )


def _send_with_smtp(recipient: str, template: Dict[str, str]) -> None:
    """
    Send email using SMTP.
    
    Creates a multipart email with both HTML and plain text versions.
    Connects to the configured SMTP server, authenticates, and sends the email.
    
    Raises:
        smtplib.SMTPAuthenticationError: If authentication fails
        smtplib.SMTPConnectError: If connection to SMTP server fails
        smtplib.SMTPException: For other SMTP-related errors
        socket.error: For network errors
    """
    logger.debug(
        "Sending email via SMTP to %s using server %s:%s",
        recipient[:3] + "***" if len(recipient) > 3 else "***",
        settings.SMTP_HOST,
        settings.SMTP_PORT
    )
    
    # Create multipart message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = template["subject"]
    msg['From'] = f"{settings.SYSTEM_EMAIL_NAME} <{settings.SYSTEM_EMAIL_FROM}>"
    msg['To'] = recipient
    
    # Add both plain text and HTML parts
    text_part = MIMEText(template["text"], 'plain', 'utf-8')
    html_part = MIMEText(template["html"], 'html', 'utf-8')
    
    msg.attach(text_part)
    msg.attach(html_part)
    
    # Connect to SMTP server and send
    try:
        # Use SSL for port 465, regular SMTP for other ports
        if settings.SMTP_PORT == 465:
            # Port 465 uses SSL from the start
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        else:
            # Port 587 uses STARTTLS
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        
        with server:
            # Enable debug output in development (level 1 = connection info)
            if settings.DEBUG:
                server.set_debuglevel(1)
            
            # Start TLS if enabled and not using SSL (port 465)
            if settings.SMTP_USE_TLS and settings.SMTP_PORT != 465:
                server.starttls()
            
            # Authenticate
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            
            # Send email
            server.send_message(msg)
            
            logger.debug("Email sent successfully via SMTP to %s", recipient[:3] + "***" if len(recipient) > 3 else "***")
    
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed for user %s", settings.SMTP_USER[:3] + "***" if len(settings.SMTP_USER) > 3 else "***")
        raise
    except smtplib.SMTPConnectError as e:
        logger.error("Failed to connect to SMTP server %s:%s: %s", settings.SMTP_HOST, settings.SMTP_PORT, str(e))
        raise
    except smtplib.SMTPException as e:
        logger.error("SMTP error occurred: %s", str(e))
        raise

